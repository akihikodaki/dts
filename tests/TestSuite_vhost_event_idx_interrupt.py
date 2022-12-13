# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
Vhost event idx interrupt need test with l3fwd-power sample
"""

import re
import time

from framework.test_case import TestCase
from framework.virt_common import VM


class TestVhostEventIdxInterrupt(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.

        """
        self.vm_num = 1
        self.queues = 1
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.prepare_l3fwd_power()
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.app_l3fwd_power_path = self.dut.apps_name["l3fwd-power"]
        self.l3fwdpower_name = self.app_l3fwd_power_path.split("/")[-1]
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.verify_info = []
        self.dut.send_expect(f"killall {self.l3fwdpower_name}", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vhost = self.dut.new_session(suite="vhost-l3fwd")
        self.vm_dut = []
        self.vm = []
        self.nopci = True

    def get_core_mask(self):
        self.core_config = "1S/%dC/1T" % (self.vm_num * self.queues)
        self.verify(
            self.cores_num >= self.queues * self.vm_num,
            "There has not enought cores to test this case %s" % self.running_case,
        )
        self.core_list_l3fwd = self.dut.get_core_list(self.core_config)

    def prepare_l3fwd_power(self):
        out = self.dut.build_dpdk_apps("examples/l3fwd-power")
        self.verify("Error" not in out, "compilation l3fwd-power error")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def lanuch_l3fwd_power(self):
        """
        launch l3fwd-power with a virtual vhost device
        """
        res = True
        self.logger.info("Launch l3fwd_sample sample:")
        config_info = ""
        core_index = 0
        # config the interrupt cores info
        for port in range(self.vm_num):
            for queue in range(self.queues):
                if config_info != "":
                    config_info += ","
                config_info += "(%d,%d,%s)" % (
                    port,
                    queue,
                    self.core_list_l3fwd[core_index],
                )
                info = {
                    "core": self.core_list_l3fwd[core_index],
                    "port": port,
                    "queue": queue,
                }
                self.verify_info.append(info)
                core_index = core_index + 1
        # config the vdev info, if have 2 vms, it shoule have 2 vdev info
        vdev_info = ""
        for i in range(self.vm_num):
            vdev_info += (
                "--vdev 'net_vhost%d,iface=%s/vhost-net%d,queues=%d,client=1' "
                % (i, self.base_dir, i, self.queues)
            )

        port_info = "0x1" if self.vm_num == 1 else "0x3"

        example_para = self.app_l3fwd_power_path + " "
        para = (
            " --log-level=9 %s -- -p %s --parse-ptype 1 --config '%s' --interrupt-only"
            % (vdev_info, port_info, config_info)
        )
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_l3fwd, no_pci=self.nopci
        )
        command_line_client = example_para + eal_params + para
        self.vhost.get_session_before(timeout=2)
        self.vhost.send_expect(command_line_client, "POWER", 40)
        time.sleep(10)
        out = self.vhost.get_session_before()
        if "Error" in out and "Error opening" not in out:
            self.logger.error("Launch l3fwd-power sample error")
            res = False
        else:
            self.logger.info("Launch l3fwd-power sample finished")
        self.verify(res is True, "Lanuch l3fwd failed")

    def relanuch_l3fwd_power(self):
        """
        relauch l3fwd-power sample for port up
        """
        self.dut.send_expect("killall -s INT %s" % self.l3fwdpower_name, "#")
        # make sure l3fwd-power be killed
        pid = self.dut.send_expect(
            "ps -ef |grep l3|grep -v grep |awk '{print $2}'", "#"
        )
        if pid:
            self.dut.send_expect("kill -9 %s" % pid, "#")
        self.lanuch_l3fwd_power()

    def set_vm_cpu_number(self, vm_config):
        # config the vcpu numbers when queue number greater than 1
        if self.queues == 1:
            return
        params_number = len(vm_config.params)
        for i in range(params_number):
            if list(vm_config.params[i].keys())[0] == "cpu":
                vm_config.params[i]["cpu"][0]["number"] = self.queues

    def check_qemu_version(self, vm_config):
        """
        in this suite, the qemu version should greater 2.7
        """
        self.vm_qemu_version = vm_config.qemu_emulator
        params_number = len(vm_config.params)
        for i in range(params_number):
            if list(vm_config.params[i].keys())[0] == "qemu":
                self.vm_qemu_version = vm_config.params[i]["qemu"][0]["path"]

        out = self.dut.send_expect("%s --version" % self.vm_qemu_version, "#")
        result = re.search("QEMU\s*emulator\s*version\s*(\d*.\d*)", out)
        self.verify(
            result is not None,
            "the qemu path may be not right: %s" % self.vm_qemu_version,
        )
        version = result.group(1)
        index = version.find(".")
        self.verify(
            int(version[:index]) > 2
            or (int(version[:index]) == 2 and int(version[index + 1 :]) >= 7),
            "This qemu version should greater than 2.7 "
            + "in this suite, please config it in vhost_sample.cfg file",
        )

    def start_vms(self, vm_num=1, packed=False):
        """
        start qemus
        """
        for i in range(vm_num):
            vm_info = VM(self.dut, "vm%d" % i, "vhost_sample")
            vm_info.load_config()
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            vm_params["opt_mac"] = "00:11:22:33:44:5%d" % i
            vm_params["opt_server"] = "server"
            if self.queues > 1:
                vm_params["opt_queue"] = self.queues
                opt_args = "csum=on,mq=on,vectors=%d" % (2 * self.queues + 2)
            else:
                opt_args = "csum=on"
            if packed:
                opt_args = opt_args + ",packed=on"
            vm_params["opt_settings"] = opt_args
            vm_info.set_vm_device(**vm_params)
            self.set_vm_cpu_number(vm_info)
            self.check_qemu_version(vm_info)
            vm_dut = None
            try:
                vm_dut = vm_info.start(load_config=False, set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                self.logger.error("ERROR: Failure for %s" % str(e))
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def config_virito_net_in_vm(self):
        """
        set vitio-net with 2 quques enable
        """
        for i in range(len(self.vm_dut)):
            vm_intf = self.vm_dut[i].ports_info[0]["intf"]
            self.vm_dut[i].send_expect(
                "ethtool -L %s combined %d" % (vm_intf, self.queues), "#", 20
            )

    def check_vhost_core_status(self, vm_index, status):
        """
        check the cpu status
        """
        out = self.vhost.get_session_before()
        for i in range(self.queues):
            # because of the verify_info include all config(vm0 and vm1)
            # so current index shoule vm_index + queue_index
            verify_index = i + vm_index
            if status == "waked up":
                info = "lcore %s is waked up from rx interrupt on port %d queue %d"
                info = info % (
                    self.verify_info[verify_index]["core"],
                    self.verify_info[verify_index]["port"],
                    self.verify_info[verify_index]["queue"],
                )
            elif status == "sleeps":
                info = (
                    "lcore %s sleeps until interrupt triggers"
                    % self.verify_info[verify_index]["core"]
                )
            self.logger.info(info)
            self.verify(info in out, "The CPU status not right for %s" % info)

    def send_and_verify(self):
        """
        start to send packets and check the cpu status
        stop and restart to send packets and check the cpu status
        """
        ping_ip = 3
        for vm_index in range(self.vm_num):
            session_info = []
            vm_intf = self.vm_dut[vm_index].ports_info[0]["intf"]
            self.vm_dut[vm_index].send_expect(
                "ifconfig %s 1.1.1.%d" % (vm_intf, ping_ip), "#"
            )
            ping_ip = ping_ip + 1
            self.vm_dut[vm_index].send_expect("ifconfig %s up" % vm_intf, "#")
            for queue in range(self.queues):
                session = self.vm_dut[vm_index].new_session(
                    suite="ping_info_%d" % queue
                )
                session.send_expect(
                    "taskset -c %d ping 1.1.1.%d" % (queue, ping_ip), "PING", 30
                )
                session_info.append(session)
                ping_ip = ping_ip + 1
            time.sleep(3)
            self.check_vhost_core_status(vm_index=vm_index, status="waked up")
            # close all sessions of ping in vm
            for sess_index in range(len(session_info)):
                session_info[sess_index].send_expect("^c", "#")
                self.vm_dut[vm_index].close_session(session_info[sess_index])

    def stop_all_apps(self):
        """
        close all vms
        """
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.dut.send_expect("killall %s" % self.l3fwdpower_name, "#", timeout=2)

    def test_wake_up_split_ring_vhost_user_core_with_event_idx_interrupt(self):
        """
        Test Case 1: wake up split ring vhost-user core with event idx interrupt mode
        """
        self.vm_num = 1
        self.queues = 1
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num)
        self.relanuch_l3fwd_power()
        self.send_and_verify()
        self.stop_all_apps()

    def test_wake_up_split_ring_vhost_user_cores_with_event_idx_interrupt_mode_16_queues(
        self,
    ):
        """
        Test Case 2: wake up split ring vhost-user cores with event idx interrupt mode 16 queues test
        """
        self.vm_num = 1
        self.queues = 16
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num)
        self.relanuch_l3fwd_power()
        self.config_virito_net_in_vm()
        self.send_and_verify()
        self.stop_all_apps()

    def test_wake_up_split_ring_vhost_user_cores_by_multi_virtio_net_in_vms_with_event_idx_interrupt(
        self,
    ):
        """
        Test Case 3: wake up split ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode
        """
        self.vm_num = 2
        self.queues = 1
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num)
        self.relanuch_l3fwd_power()
        self.send_and_verify()
        self.stop_all_apps()

    def test_wake_up_packed_ring_vhost_user_core_with_event_idx_interrupt(self):
        """
        wake up vhost-user core with l3fwd-power sample
        """
        self.vm_num = 1
        self.queues = 1
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num, packed=True)
        self.relanuch_l3fwd_power()
        self.send_and_verify()
        self.stop_all_apps()

    def test_wake_up_packed_ring_vhost_user_cores_with_event_idx_interrupt_mode_16_queues(
        self,
    ):
        """
        Test Case 5: wake up packed ring vhost-user cores with event idx interrupt mode 16 queues test
        """
        self.vm_num = 1
        self.queues = 16
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num, packed=True)
        self.relanuch_l3fwd_power()
        self.config_virito_net_in_vm()
        self.send_and_verify()
        self.stop_all_apps()

    def test_wake_up_packed_ring_vhost_user_cores_by_multi_virtio_net_in_vms_with_event_idx_interrupt(
        self,
    ):
        """
        Test Case 6: wake up packed ring vhost-user cores by multi virtio-net in VMs with event idx interrupt mode
        """
        self.vm_num = 2
        self.queues = 1
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num, packed=True)
        self.relanuch_l3fwd_power()
        self.send_and_verify()
        self.stop_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.close_session(self.vhost)
        self.dut.send_expect(f"killall {self.l3fwdpower_name}", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
