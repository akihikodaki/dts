# BSD LICENSE
#
# Copyright(c) 2010-2020 Intel Corporation. All rights reserved.
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
power negative test suite.
"""

import os
import re
import time
import traceback

from framework.exception import VerifyFailure
from framework.qemu_libvirt import LibvirtKvm
from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestPowerNegative(TestCase):
    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = (
            "/root" + self.dut.base_dir[1:]
            if self.dut.base_dir.startswith("~")
            else self.dut.base_dir
        )
        return target_dir

    def prepare_binary(self, name, host_crb=None):
        _host_crb = host_crb if host_crb else self.dut
        example_dir = "examples/" + name
        out = _host_crb.build_dpdk_apps("./" + example_dir)
        return os.path.join(
            self.target_dir, _host_crb.apps_name[os.path.basename(name)]
        )

    def add_console(self, session):
        self.ext_con[session.name] = [
            session.send_expect,
            session.session.get_output_all,
        ]

    def get_console(self, name):
        default_con_table = {
            self.dut.session.name: [self.dut.send_expect, self.dut.get_session_output],
            self.dut.alt_session.name: [
                self.dut.alt_session.send_expect,
                self.dut.alt_session.session.get_output_all,
            ],
        }
        if name not in default_con_table:
            return self.ext_con.get(name) or [None, None]
        else:
            return default_con_table.get(name)

    def execute_cmds(self, cmds, name="dut"):
        console, msg_pipe = self.get_console(name)
        if len(cmds) == 0:
            return
        if isinstance(cmds, str):
            cmds = [cmds, "# ", 5]
        if not isinstance(cmds[0], list):
            cmds = [cmds]
        outputs = [] if len(cmds) > 1 else ""
        for item in cmds:
            expected_items = item[1]
            if expected_items and isinstance(expected_items, (list, tuple)):
                expected_str = expected_items[0] or "# "
            else:
                expected_str = expected_items or "# "

            try:
                if len(item) == 3:
                    timeout = int(item[2])
                    output = console(item[0], expected_str, timeout)
                    output = msg_pipe() if not output else output
                else:
                    output = console(item[0], expected_str)
                    output = msg_pipe() if not output else output
            except Exception as e:
                msg = "execute '{0}' timeout".format(item[0])
                raise Exception(msg)
            time.sleep(1)
            if len(cmds) > 1:
                outputs.append(output)
            else:
                outputs = output

        return outputs

    def d_con(self, cmds):
        return self.execute_cmds(cmds, name=self.dut.session.name)

    def d_a_con(self, cmds):
        return self.execute_cmds(cmds, name=self.dut.alt_session.name)

    def vm_con(self, cmds):
        return self.execute_cmds(cmds, name=self.vm_dut.session.name)

    def vm_g_con(self, cmds):
        return self.execute_cmds(cmds, name=self.guest_con_name)

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con("cat " + drv_file)
        if not output:
            msg = "unknown power driver"
            self.verify(False, msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    @property
    def is_support_pbf(self):
        # check if cpu support bpf feature
        cpu_attr = r"/sys/devices/system/cpu/cpu0/cpufreq/base_frequency"
        cmd = "ls {0}".format(cpu_attr)
        self.d_a_con(cmd)
        cmd = "echo $?"
        output = self.d_a_con(cmd)
        ret = True if output == "0" else False
        return ret

    def get_all_cpu_attrs(self):
        """
        get all cpus' base_frequency value, if not support pbf, set all to 0
        """
        if not self.is_support_pbf:
            cpu_topos = self.dut.get_all_cores()
            _base_freqs_info = {}
            for index, _ in enumerate(cpu_topos):
                _base_freqs_info[index] = 0
            return _base_freqs_info
        # if cpu support high priority core
        key_values = ["base_frequency", "cpuinfo_max_freq", "cpuinfo_min_freq"]
        freq = r"/sys/devices/system/cpu/cpu{0}/cpufreq/{1}".format
        # use dut alt session to get dut platform cpu base frequency attribute
        cpu_topos = self.dut.get_all_cores()
        cpu_info = {}
        for cpu_topo in cpu_topos:
            cpu_id = int(cpu_topo["thread"])
            cpu_info[cpu_id] = {}
            cpu_info[cpu_id]["socket"] = cpu_topo["socket"]
            cpu_info[cpu_id]["core"] = cpu_topo["core"]

        for key_value in key_values:
            cmds = []
            for cpu_id in sorted(cpu_info.keys()):
                cmds.append("cat {0}".format(freq(cpu_id, key_value)))
            output = self.d_a_con(";".join(cmds))
            freqs = [int(item) for item in output.splitlines()]
            for index, cpu_id in enumerate(sorted(cpu_info.keys())):
                cpu_info[cpu_id][key_value] = freqs[index]

        # get high priority core and normal core
        base_freqs_info = {}
        for core_index, value in cpu_info.items():
            base_frequency = value.get("base_frequency")
            base_freqs_info.setdefault(base_frequency, []).append(core_index)
        base_freqs = list(base_freqs_info.keys())
        # cpu should have high priority core and normal core
        # high priority core frequency is higher than normal core frequency
        if len(base_freqs) <= 1 or not all(
            [len(value) for value in list(base_freqs_info.values())]
        ):
            msg = "current cpu has no high priority core"
            raise Exception(msg)

        high_pri_freq = max(self.base_freqs_info.keys())
        high_pri_cores = base_freqs_info[high_pri_freq]
        _base_freqs_info = {}
        for index, _ in enumerate(cpu_topos):
            _base_freqs_info[index] = 1 if index in high_pri_cores else 0

        return _base_freqs_info

    def init_vms_params(self):
        self.vm = (
            self.vcpu_map
        ) = (
            self.vcpu_lst
        ) = self.vm_dut = self.guest_session = self.is_guest_on = self.is_vm_on = None
        # vm config
        self.vm_name = "vm0"
        self.vm_max_ch = 8
        self.vm_log_dir = "/tmp/powermonitor"
        self.create_powermonitor_folder()

    def create_powermonitor_folder(self):
        # create temporary folder for power monitor
        cmd = "mkdir -p {0}; chmod 777 {0}".format(self.vm_log_dir)
        self.d_a_con(cmd)

    def start_vm(self):
        # set vm initialize parameters
        self.init_vms_params()
        # start vm
        self.vm = LibvirtKvm(self.dut, self.vm_name, self.suite_name)
        # pass pf to virtual machine
        pci_addr = self.dut.get_port_pci(self.dut_ports[0])
        # add channel
        ch_name = "virtio.serial.port.poweragent.{0}"
        vm_path = os.path.join(self.vm_log_dir, "{0}.{1}")
        for cnt in range(self.vm_max_ch):
            channel = {
                "path": vm_path.format(self.vm_name, cnt),
                "name": ch_name.format(cnt),
            }
            self.vm.add_vm_virtio_serial_channel(**channel)
        # boot up vm
        self.vm_dut = self.vm.start()
        self.is_vm_on = True
        self.verify(self.vm_dut, "create vm_dut fail !")
        self.add_console(self.vm_dut.session)
        # get virtual machine cpu cores
        _vcpu_map = self.vm.get_vm_cpu()
        self.vcpu_map = [int(item) for item in _vcpu_map]
        self.vcpu_lst = [int(item["core"]) for item in self.vm_dut.cores]

    def close_vm(self):
        # close vm
        if self.is_vm_on:
            if self.guest_session:
                self.vm_dut.close_session(self.guest_session)
                self.guest_session = None
            self.vm.stop()
            self.is_vm_on = False
            self.vm = None
            self.dut.virt_exit()
            cmd_fmt = "virsh {0} {1} > /dev/null 2>&1".format
            cmds = [
                [cmd_fmt("shutdown", self.vm_name), "# "],
                [cmd_fmt("undefine", self.vm_name), "# "],
            ]
            self.d_a_con(cmds)

    def init_testpmd(self):
        self.testpmd = "/root/dpdk/x86_64-native-linuxapp-gcc/app/dpdk-testpmd"

    def close_testpmd(self):
        if not self.is_testpmd_on:
            return
        self.logger.info("closing testpmd ..")
        self.d_con(["quit", "# ", 15])
        self.is_testpmd_on = False

    def init_vm_power_mgr(self):
        self.vm_power_mgr = self.prepare_binary("vm_power_manager")

    def close_vm_power_mgr(self):
        if not self.is_mgr_on:
            return
        self.logger.info("closing vm_power_mgr ..")
        self.d_con(["quit", "# ", 15])
        self.is_mgr_on = False

    def init_guest_mgr(self):
        name = "vm_power_manager/guest_cli"
        self.guest_cli = self.prepare_binary(name, host_crb=self.vm_dut)
        self.guest_con_name = "_".join([self.vm_dut.NAME, name.replace("/", "-")])
        self.guest_session = self.vm_dut.create_session(self.guest_con_name)
        self.add_console(self.guest_session)

    def close_guest_mgr(self):
        if not self.is_guest_on:
            return
        self.logger.info("closing guest_mgr ..")
        self.vm_g_con("quit")
        self.is_guest_on = False

    def check_cpupower_tool(self):
        cmd = "whereis cpupower > /dev/null 2>&1; echo $?"
        output = self.d_a_con(cmd)
        status = True if output and output.strip() == "0" else False
        msg = "cpupower tool have not installed on DUT"
        self.verify(status, msg)

    def verify_power_driver(self):
        expected_drv = "acpi-cpufreq"
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv
        )
        self.verify(power_drv == expected_drv, msg)

    def preset_test_environment(self):
        self.is_mgr_on = None
        self.ext_con = {}
        # modprobe msr module to let the application can get the CPU HW info
        self.d_a_con("modprobe msr")
        self.d_a_con("cpupower frequency-set -g userspace")
        self.dut.init_core_list_uncached_linux()
        # check if cpu support bpf feature
        self.base_freqs_info = self.get_all_cpu_attrs()
        # boot up vm
        self.start_vm()
        # init binary
        self.init_vm_power_mgr()
        self.init_guest_mgr()
        self.init_testpmd()

    def verify_inject_malformed_json_to_fifo_channel(self):
        # Test Case1: Inject Malformed JSON Command file to fifo channel
        # 1. Create powermonitor fold for vm_power_manager sample::
        #     mkdir /tmp/powermonitor
        #     chmod 777 /tmp/powermonitor
        # 2. Launch VM power manager sample::
        #     ./examples/vm_power_manager/build/vm_power_mgr -l 1-3 -n 4 --file-prefix=test1 --no-pci
        # 3. Prepare policy in JSON format then send it to the fifo channel:
        #     Prepare different command in JSON format then send it to the fifo channel
        #     Modify "name", "resource_id", "command" to large character string to check if the vm_power_mgr sample will crash
        #     For example::
        #       {"policy": {
        #         "name": "01234567890123445678901234567890123456789001234567890",
        #         "command": "create",
        #         "policy_type": "WORKLOAD",
        #         "workload": "MEDIUM",
        #         "core_list":[ 22]
        #       }}
        # 4. Send Json format command to the fifo channel::
        #     cat command.json >/tmp/powermonitor/fifo1

        # start vm_power_mgr
        option = " -v -l 1-3 -n 4 --file-prefix=test1 --no-pci "
        cmd = [" ".join([self.vm_power_mgr, option]), "vmpower> ", 30]
        self.d_con(cmd)
        self.is_mgr_on = True

        # prepare an send the json file to fifo
        echo_json = (
            'echo {\\"policy\\": {'
            '  \\"name\\": \\"01234567890123445678901234567890123456789001234567890\\",'
            '  \\"command\\": \\"create\\",'
            '  \\"policy_type\\": \\"WORKLOAD\\",'
            '  \\"workload\\": \\"MEDIUM\\"'
            "}} > /tmp/command.json;"
        )
        cat_json = "cat /tmp/command.json > /tmp/powermonitor/fifo1"
        self.d_a_con([" ".join([echo_json, cat_json]), "# ", 10])

        out = self.d_con(["show_cpu_freq 1", "vmpower> ", 20])
        self.verify(
            "Core 1 frequency:" in out, "vm_power_manager did not work as expected"
        )

    def verify_send_invalid_cmd_through_json_chn(self):
        # Test Case2 : Send invalid command through JSON channel
        # 1. Create powermonitor fold for vm_power_manager sample::
        #     mkdir /tmp/powermonitor
        #     chmod 777 /tmp/powermonitor
        # 2. Launch VM power manager sample::
        #     ./examples/vm_power_manager/build/vm_power_mgr -l 1-3 -n 4 --file-prefix=test1 --no-pci
        # 3. Prepare policy in JSON format then send it to the fifo channel:
        #     Prepare invalid power command, for example, core list above the max core number.
        #     For example::
        #       {"policy": {
        #         "name": "Ubuntu",
        #         "command": "create",
        #         "policy_type": "WORKLOAD",
        #         "workload": "MEDIUM_111"
        #       }}
        #       {"policy": {
        #         "name": "Ubuntu",
        #         "command": "create",
        #         "policy_type": "WORKLOAD_111",
        #         "workload": "MEDIUM"
        #       }}
        # 4. Send Json format command to the fifo channel::
        # 	cat command.json >/tmp/powermonitor/fifo1

        # start vm_power_mgr
        option = " -v -l 1-3 -n 4 --file-prefix=test1 --no-pci "
        cmd = [" ".join([self.vm_power_mgr, option]), "vmpower>", 30]
        self.d_con(cmd)
        self.is_mgr_on = True

        # prepare an sen the json file to fifo
        echo_json = (
            'echo {\\"policy\\": {'
            '  \\"name\\": \\"Ubuntu\\",'
            '  \\"command\\": \\"create\\",'
            '  \\"policy_type\\": \\"WORKLOAD\\",'
            '  \\"workload\\": \\"MEDIUM_111\\"'
            "}} > /tmp/command.json;"
        )
        cat_json = "cat /tmp/command.json > /tmp/powermonitor/fifo1"
        out = self.d_con(["show_cpu_freq 1", "vmpower>", 20])
        self.verify(
            "Core 1 frequency:" in out, "vm_power_manager did not work as expected"
        )

        self.d_a_con([" ".join([echo_json, cat_json]), "#", 10])
        echo_json = (
            'echo {\\"policy\\": {'
            '  \\"name\\": \\"Ubuntu\\",'
            '  \\"command\\": \\"create\\",'
            '  \\"policy_type\\": \\"WORKLOAD_111\\",'
            '  \\"workload\\": \\"MEDIUM\\"'
            "}} > /tmp/command.json;"
        )
        cat_json = "cat /tmp/command.json > /tmp/powermonitor/fifo1"
        self.d_a_con([" ".join([echo_json, cat_json]), "#", 10])

        out = self.d_con(["show_cpu_freq 1", "vmpower>", 20])
        self.verify(
            "Core 1 frequency:" in out, "vm_power_manager did not work as expected"
        )

    def verify_host_power_check_policy_from_untrusted_vm(self):
        # Test Case3 : Send malformed command to host power daemon app
        # 1. Launch VM by using libvirt, one NIC should be configured as PCI pass-throughput to the VM::
        # virsh start [VM name]
        # 2. Launch VM power manager sample on the host to monitor the channel from VM::
        # ./examples/vm_power_manager/build/vm_power_mgr -l 12-14 -n 4 --no-pci
        # >　add_vm [vm name]
        # >　add_channels [vm name] all
        # >　set_channel_status [vm name] all enabled
        # >　show_vm [vm name]
        # Check the invalid input command for vm_power_mgr sample::
        # > add_channels ubuntu 128
        # > add_channel ubuntu 10000000000000000
        # 3. In the VM, launch guest_vm_power_mgr to set and send the power manager policy to the host power sample::
        # ./examples/vm_power_manager/guest_cli/build/guest_vm_power_mgr -c 0xff -n 4 -m 1024 --no-pci --file-prefix=yaolei \
        # -- --vm-name=ubuntu --vcpu-list=0-7
        # > set_cpu_freq 128 down
        # > set_cpu_freq 1000000000000 down
        # > set_cpu_freq -1 down
        # also try other commands::
        # "<up|down|min|max|enable_turbo|disable_turbo>"
        # Check point:　No crash should be occur at vm_power_mgr sample

        # start vm_power_mgr
        option = " -v -l 1-3 -n 4 --file-prefix=test1 --no-pci "
        cmd = [" ".join([self.vm_power_mgr, option]), "vmpower>", 30]
        self.d_con(cmd)
        self.is_mgr_on = True

        self.d_con(["add_vm {}".format(self.vm_name), "vmpower>", 5])
        self.d_con(["add_channels {} all".format(self.vm_name), "vmpower>", 5])
        self.d_con(["add_channels_status {} all".format(self.vm_name), "vmpower>", 5])
        vm_info = self.d_con(["show_vm {}".format(self.vm_name), "vmpower>", 5])
        self.verify("CONNECTED" in vm_info, "vm_power_manager did not work as expected")

        out = self.d_con(["add_channels ubuntu 128", "vmpower>", 5])
        self.verify(
            "Segmentation fault" not in out and "core dump" not in out,
            "Segmentation fault or core dumped happened",
        )

        out = self.d_con(["add_channel ubuntu 10000000000000000", "vmpower>", 5])
        self.verify(
            "Segmentation fault" not in out and "core dump" not in out,
            "Segmentation fault or core dumped happened",
        )

        # start vm_power_mgr
        prompt = r"vmpower\(guest\)>"
        vm_pwr_quest = (
            self.guest_cli
            + " -v -c 0xff -n 4 -m 1024 --no-pci --file-prefix=yaolei -- --vm-name=ubuntu --vcpu-list=0-7 "
        )
        self.vm_g_con([vm_pwr_quest, prompt, 120])
        self.is_guest_on = True

        commands = ["up", "down", "min", "max", "enable_turbo", "disable_turbo"]
        numbers = ["128", "1000000000000", "-1"]
        for command in commands:
            for number in numbers:
                cmd_line = "set_cpu_freq {} {}".format(number, command)
                out = self.vm_g_con([cmd_line, prompt, 10])
                self.logger.info("vmpower(guest)> {} --> out: {}".format(cmd_line, out))
                self.verify(
                    "Segmentation fault" not in out and "core dump" not in out,
                    "Segmentation fault or core dumped happened",
                )

    def verify_traffic_policy_test_based_on_json(self):
        # Test Case4 : TRAFFIC Policy Test based on JSON configure file with large integer number
        # ========================================================================================
        # Step1. Generate 1 VF under igb_uio driver, launch vm_power_mgr sample with PF, for example:
        # 	echo 1 > /sys/bus/pci/drivers/igb_uio/0000\:82\:00.0/max_vfs
        # 	./examples/vm_power_manager/build/vm_power_mgr -l 1-4 -n 4 --socket-mem=1024,1024 --file-prefix=test1 -a 82:00.0 -- -p 0x01
        # Step 2. Launch testpmd with VF
        # 	./x86_64-native-linuxapp-gcc/app/testpmd -l 5-6 -n 4 --socket-mem=1024,1024 --file-prefix=test2 -a 0000:82:02.0 -- -i
        # 	>set fwd macswap
        # 	>start
        # Step 3. Prepare traffic policy in JSON format then send it to the power demon sample, put the VF MAC into the mac_list:
        # 	{"policy": {
        # 	  "name": "ubuntu",
        # 	  "command": "create",
        # 	  "policy_type": "TRAFFIC",
        #     "max_packet_thresh": 500000000000000000000000000000,
        # 	  "avg_packet_thresh": 300000000000000000000000000000,
        # 	  "mac_list":[ "E0:E0:E0:E0:F0:F0"]
        # 	}}
        # 	cat traffic.json >/tmp/powermonitor/fifo3
        # Check point:　No crash should be occur at vm_power_mgr sample

        # self.d_con(['echo 1 > /sys/bus/pci/drivers/igb_uio/0000\:82\:00.0/max_vfs', '#', 10])
        self.d_con(
            [
                f'echo 1 > "/sys/bus/pci/drivers/vfio-pci/{self.port_pci}/sriov_numvfs"',
                "#",
                10,
            ]
        )

        # start vm_power_mgr
        cmd = f"{self.vm_power_mgr} -l 1-4 -n 4 --socket-mem=1024,1024 --file-prefix=test1 -a {self.port_pci} -- -p 0x01"
        self.d_a_con([cmd, "vmpower>", 30])
        self.is_mgr_on = True

        vm_info = self.d_a_con(["show_cpu_freq 1", "vmpower>", 5])
        self.logger.info(vm_info)

        # Step 2.  Launch testpmd with VF
        cmd = f"{self.testpmd} -l 5-6 -n 4 --socket-mem=1024,1024 --file-prefix=test2 -a {self.port_pci} -- -i"
        self.d_con([cmd, "testpmd>", 30])
        self.is_testpmd_on = True

        self.d_con(["set fwd macswap", "testpmd>", 5])
        self.d_con(["start", "testpmd>", 5])
        self.close_testpmd()

        # prepare an sen the json file to fifo
        echo_json = (
            'echo {\\"policy\\": {'
            '  \\"name\\": \\"ubuntu\\",'
            '  \\"command\\": \\"create\\",'
            '  \\"policy_type\\": \\"TRAFFIC\\",'
            '  \\"max_packet_thresh\\": 500000000000000000000000000000,'
            '  \\"avg_packet_thresh\\": 300000000000000000000000000000,'
            '  \\"mac_list\\":[ \\"E0:E0:E0:E0:F0:F0\\"]'
            "}} > /tmp/traffic.json;"
        )
        cat_json = "cat /tmp/traffic.json > /tmp/powermonitor/fifo3"
        self.d_con([" ".join([echo_json, cat_json]), "#", 10])

        # Check point:　No crash should be occur at vm_power_mgr sample
        out = self.d_a_con(["show_cpu_freq 1", "vmpower>", 5])
        self.d_a_con(["quit", "# ", 15])
        self.is_mgr_on = False

        self.verify(
            "Segmentation fault" not in out and "core dump" not in out,
            "Segmentation fault or core dumped happened",
        )

    #################
    #
    # Test cases.
    #
    #################

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Not enough ports")
        self.check_cpupower_tool()
        self.verify_power_driver()
        # prepare testing environment
        self.preset_test_environment()
        self.port_pci = self.dut.get_port_pci(self.dut_ports[0])

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_vm()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_vm_power_mgr()
        self.close_guest_mgr()
        self.vm_dut.kill_all()
        self.dut.kill_all()

    def test_inject_malformed_json_to_fifo_channel(self):
        """
        Inject Malformed Json Command file to fifo channel
        """
        self.verify_inject_malformed_json_to_fifo_channel()

    def test_send_invalid_cmd_through_json_chn(self):
        """
        Send invalid command through JSON channel
        """
        self.verify_send_invalid_cmd_through_json_chn()

    def test_host_power_check_policy_from_untrusted_vm(self):
        """
        Check if host power APP have check point for the power policy sent from untrusted VM

        """
        self.verify_host_power_check_policy_from_untrusted_vm()

    def test_traffic_policy_test_based_on_json(self):
        """
        TRAFFIC Policy Test based on JSON configure file with large integer number

        """
        self.verify_traffic_policy_test_based_on_json()
