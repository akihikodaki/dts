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
power bidirection channel test suite.
"""
import os
import time
import traceback

from utils import create_mask as dts_create_mask
from qemu_libvirt import LibvirtKvm
from exception import VerifyFailure
from test_case import TestCase


class TestPowerBidirectionChannel(TestCase):

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def get_cores_mask(self, config='all'):
        ports_socket = self.dut.get_numa_id(self.dut.get_ports()[0])
        mask = dts_create_mask(
            self.dut.get_core_list(config, socket=ports_socket))
        return mask

    def prepare_binary(self, name, host_crb=None):
        _host_crb = host_crb if host_crb else self.dut
        example_dir = "examples/" + name
        out = _host_crb.build_dpdk_apps('./' + example_dir)
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        binary_dir = os.path.join(self.target_dir, example_dir, 'build')
        cmd = ["ls -F {0} | grep '*'".format(binary_dir), '# ', 5]
        exec_file = self.execute_cmds(cmd, name=_host_crb.session.name)
        binary_file = os.path.join(binary_dir, exec_file[:-1])
        return binary_file

    def add_console(self, session):
        self.ext_con[session.name] = [
            session.send_expect,
            session.session.get_output_all]

    def get_console(self, name):
        default_con_table = {
            self.dut.session.name: [
                self.dut.send_expect,
                self.dut.get_session_output],
            self.dut.alt_session.name: [
                self.dut.alt_session.send_expect,
                self.dut.alt_session.session.get_output_all]}
        if name not in default_con_table:
            return self.ext_con.get(name) or [None, None]
        else:
            return default_con_table.get(name)

    def execute_cmds(self, cmds, name='dut'):
        console, msg_pipe = self.get_console(name)
        if len(cmds) == 0:
            return
        if isinstance(cmds, str):
            cmds = [cmds, '# ', 5]
        if not isinstance(cmds[0], list):
            cmds = [cmds]
        outputs = [] if len(cmds) > 1 else ''
        for item in cmds:
            expected_items = item[1]
            if expected_items and isinstance(expected_items, (list, tuple)):
                expected_str = expected_items[0] or '# '
            else:
                expected_str = expected_items or '# '

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
        output = self.d_a_con('cat ' + drv_file)
        if not output:
            msg = 'unknown power driver'
            self.verify(False, msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    @property
    def is_support_pbf(self):
        # check if cpu support bpf feature
        cpu_attr = r'/sys/devices/system/cpu/cpu0/cpufreq/base_frequency'
        cmd = "ls {0}".format(cpu_attr)
        self.d_a_con(cmd)
        cmd = "echo $?"
        output = self.d_a_con(cmd)
        ret = True if output == "0" else False
        return ret

    def get_all_cpu_attrs(self):
        '''
        get all cpus' base_frequency value, if not support pbf, set all to 0
        '''
        if not self.is_support_pbf:
            cpu_topos = self.dut.get_all_cores()
            _base_freqs_info = {}
            for index, _ in enumerate(cpu_topos):
                _base_freqs_info[index] = 0
            return _base_freqs_info
        # if cpu support high priority core
        key_values = ['base_frequency',
                      'cpuinfo_max_freq',
                      'cpuinfo_min_freq']
        freq = r'/sys/devices/system/cpu/cpu{0}/cpufreq/{1}'.format
        # use dut alt session to get dut platform cpu base frequency attribute
        cpu_topos = self.dut.get_all_cores()
        cpu_info = {}
        for cpu_topo in cpu_topos:
            cpu_id = int(cpu_topo['thread'])
            cpu_info[cpu_id] = {}
            cpu_info[cpu_id]['socket'] = cpu_topo['socket']
            cpu_info[cpu_id]['core'] = cpu_topo['core']

        for key_value in key_values:
            cmds = []
            for cpu_id in sorted(cpu_info.keys()):
                cmds.append('cat {0}'.format(freq(cpu_id, key_value)))
            output = self.d_a_con(';'.join(cmds))
            freqs = [int(item) for item in output.splitlines()]
            for index, cpu_id in enumerate(sorted(cpu_info.keys())):
                cpu_info[cpu_id][key_value] = freqs[index]

        # get high priority core and normal core
        base_freqs_info = {}
        for core_index, value in cpu_info.items():
            base_frequency = value.get('base_frequency')
            base_freqs_info.setdefault(base_frequency, []).append(core_index)
        base_freqs = list(base_freqs_info.keys())
        # cpu should have high priority core and normal core
        # high priority core frequency is higher than normal core frequency
        if len(base_freqs) <= 1 or \
           not all([len(value) for value in list(base_freqs_info.values())]):
            msg = 'current cpu has no high priority core'
            raise Exception(msg)

        high_pri_freq = max(self.base_freqs_info.keys())
        high_pri_cores = base_freqs_info[high_pri_freq]
        _base_freqs_info = {}
        for index, _ in enumerate(cpu_topos):
            _base_freqs_info[index] = 1 if index in high_pri_cores else 0

        return _base_freqs_info

    def init_vms_params(self):
        self.vm = self.vcpu_map = self.vcpu_lst = self.vm_dut = \
            self.guest_session = self.is_guest_on = self.is_vm_on = None
        # vm config
        self.vm_name = 'vm0'
        self.vm_max_ch = 8
        self.vm_log_dir = '/tmp/powermonitor'
        self.create_powermonitor_folder()

    def create_powermonitor_folder(self):
        # create temporary folder for power monitor
        cmd = 'mkdir -p {0}; chmod 777 {0}'.format(self.vm_log_dir)
        self.d_a_con(cmd)

    def start_vm(self):
        # set vm initialize parameters
        self.init_vms_params()
        # start vm
        self.vm = LibvirtKvm(self.dut, self.vm_name, self.suite_name)
        # pass pf to virtual machine
        pci_addr = self.dut.get_port_pci(self.dut_ports[0])
        # add channel
        ch_name = 'virtio.serial.port.poweragent.{0}'
        vm_path = os.path.join(self.vm_log_dir, '{0}.{1}')
        for cnt in range(self.vm_max_ch):
            channel = {
                'path': vm_path.format(self.vm_name, cnt),
                'name': ch_name.format(cnt)}
            self.vm.add_vm_virtio_serial_channel(**channel)
        # boot up vm
        self.vm_dut = self.vm.start()
        self.is_vm_on = True
        self.verify(self.vm_dut, "create vm_dut fail !")
        self.add_console(self.vm_dut.session)
        # get virtual machine cpu cores
        _vcpu_map = self.vm.get_vm_cpu()
        self.vcpu_map = [int(item) for item in _vcpu_map]
        self.vcpu_lst = [int(item['core']) for item in self.vm_dut.cores]

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
            cmd_fmt = 'virsh {0} {1} > /dev/null 2>&1'.format
            cmds = [
                [cmd_fmt('shutdown', self.vm_name), '# '],
                [cmd_fmt('undefine', self.vm_name), '# '], ]
            self.d_a_con(cmds)

    def init_vm_power_mgr(self):
        self.vm_power_mgr = self.prepare_binary('vm_power_manager')

    def start_vm_power_mgr(self):
        option = (
            ' -v '
            '-c {core_mask} '
            '-n {mem_channel} '
            '--no-pci ').format(**{
                'core_mask': self.get_cores_mask("1S/3C/1T"),
                'mem_channel': self.dut.get_memory_channels(), })
        prompt = 'vmpower>'
        cmd = [' '.join([self.vm_power_mgr, option]), prompt, 30]
        self.d_con(cmd)
        self.is_mgr_on = True

    def set_vm_power_mgr(self):
        vm_name = self.vm_name
        cmds = [
            "add_vm %s" % vm_name,
            "add_channels %s all" % vm_name,
            'set_channel_status %s all enabled' % vm_name,
            "show_vm %s" % vm_name]
        prompt = 'vmpower>'
        self.d_con([[cmd, prompt] for cmd in cmds])

    def close_vm_power_mgr(self):
        if not self.is_mgr_on:
            return
        self.d_con(['quit', '# ', 15])
        self.is_mgr_on = False

    def host_set_query_enable(self):
        return self.d_con(
            ['set_query {} enable'.format(self.vm_name), 'vmpower>', 15])

    def host_set_query_disable(self):
        return self.d_con(
            ['set_query {} disable'.format(self.vm_name), 'vmpower>', 15])

    def init_guest_mgr(self):
        name = 'vm_power_manager/guest_cli'
        self.guest_cli = self.prepare_binary(name, host_crb=self.vm_dut)
        self.guest_con_name = \
            '_'.join([self.vm_dut.NAME, name.replace('/', '-')])
        self.guest_session = self.vm_dut.create_session(self.guest_con_name)
        self.add_console(self.guest_session)

    def start_guest_mgr(self):
        prompt = r"vmpower\(guest\)>"
        option = (
            ' -v '
            '-c {core_mask} '
            '-n {memory_channel} '
            '-m {memory_size} '
            '--no-pci '
            '--file-prefix={file_prefix} '
            '-- '
            '--vm-name={vm_name} '
            '--vcpu-list={vpus} ').format(**{
                'core_mask': '0xff',
                'memory_channel': self.vm_dut.get_memory_channels(),
                'memory_size': 1024,
                'file_prefix': 'vmpower1',
                'vm_name': self.vm_name,
                'vpus': ','.join([str(core) for core in self.vcpu_lst]),
            })
        guest_cmd = self.guest_cli + option
        self.vm_g_con([guest_cmd, prompt, 120])
        self.is_guest_on = True

    def close_guest_mgr(self):
        if not self.is_guest_on:
            return
        self.vm_g_con("quit")
        self.is_guest_on = False

    def guest_set_cpu_freq_down(self, core_index):
        return self.vm_g_con(['set_cpu_freq {} down'.format(core_index),
                              r"vmpower\(guest\)>", 20])

    def guest_query_cpu_caps(self, core='all'):
        return self.vm_g_con(
            ['query_cpu_caps {}'.format(core), r"vmpower\(guest\)>", 20])

    def guest_query_cpu_freq(self, core='all'):
        return self.vm_g_con(
            ['query_cpu_freq {}'.format(core), r"vmpower\(guest\)>", 20])

    def run_test_pre(self):
        # boot up binary processes
        self.start_vm_power_mgr()
        # set binary process command
        self.set_vm_power_mgr()
        # boot up binary processes
        self.start_guest_mgr()

    def run_test_post(self):
        # close all binary processes
        self.close_guest_mgr()
        self.close_vm_power_mgr()

    def check_cpupower_tool(self):
        cmd = "whereis cpupower > /dev/null 2>&1; echo $?"
        output = self.d_a_con(cmd)
        status = True if output and output.strip() == "0" else False
        msg = 'cpupower tool have not installed on DUT'
        self.verify(status, msg)

    def check_policy_command_acked_output(self):
        output = self.guest_set_cpu_freq_down(self.vcpu_lst[-1])
        expected = 'ACK received for message sent to host'
        msg = "expected message '{}' not in output".format(expected)
        status = expected in output
        [self.logger.info(output) if not status else None]
        self.verify(status, msg)
        output = self.guest_set_cpu_freq_down(self.vcpu_lst[-1] + 1)
        expected = 'Error sending message: Unknown error -1'
        msg = "expected message '{}' not in output".format(expected)
        status = expected in output
        [self.logger.info(output) if not status else None]
        self.verify(status, msg)

    def check_query_cpu_freqs_command(self):
        # Query the CPU frequency for all CPU cores from VM side
        self.host_set_query_enable()

        def get_cpu_attribute(cores):
            freq_path_fmt = ("cat /sys/devices/system/cpu/cpu{0}"
                             "/cpufreq/cpuinfo_cur_freq").format
            cmd = ";".join([freq_path_fmt(core) for core in cores])
            output = self.d_a_con(cmd)
            freqs = [int(item) for item in output.splitlines()]
            return freqs

        def check(core, freq, output):
            expected = "Frequency of [{0}] vcore is {1}.".format(core, freq)
            msg = "expected message '{}' not in output".format(expected)
            self.verify(expected in output, msg)
        # check one core
        check_core = self.vcpu_lst[-1]
        freqs = get_cpu_attribute([self.vcpu_map[-1]])
        output = self.guest_query_cpu_freq(check_core)
        check(check_core, freqs[0], output)
        # check all cores
        freqs = get_cpu_attribute(self.vcpu_map)
        output = self.guest_query_cpu_freq()
        [check(check_core, freqs[index], output)
         for index, check_core in enumerate(self.vcpu_lst)]
        # disable query permission from VM, check the host CPU frequency
        # won't be returned
        self.host_set_query_disable()
        output = self.guest_query_cpu_freq()
        expected = "Error during frequency list reception."
        msg = "expected message '{}' not in output".format(expected)
        self.verify(expected in output, msg)

    def check_cpu_capability_on_vm(self):
        self.host_set_query_enable()
        # check the high priority core is recognized correctly.
        turbo_status = 1

        def check(index, output):
            vcore = self.vcpu_lst[index]
            pcore = self.vcpu_map[index]
            pri = self.base_freqs_info[pcore]
            expected = (
                "Capabilities of [{0}] vcore are: "
                "turbo possibility: {1}, "
                "is priority core: {2}.").format(vcore, turbo_status, pri)
            msg = "expected message '{}' not in output".format(expected)
            self.verify(expected in output, msg)

        output = self.guest_query_cpu_caps()
        [check(index, output)
         for index, _ in enumerate(self.vcpu_lst)]
        # check no CPU info will be return.
        output = self.guest_query_cpu_caps(self.vcpu_lst[-1] + 1)
        expected = 'Invalid parameter provided'
        msg = "expected message '{}' not in output".format(expected)
        self.verify(expected in output, msg)
        # check the host CPU capability won't be returned.
        self.host_set_query_disable()
        output = self.guest_query_cpu_caps()
        expected = "Error during capabilities reception"
        msg = "expected message '{}' not in output".format(expected)
        self.verify(expected in output, msg)

    def verify_policy_command_acked_action(self):
        except_content = None
        msg = "begin test policy command acked action ..."
        self.logger.info(msg)
        try:
            self.run_test_pre()
            self.check_policy_command_acked_output()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        msg = "test policy command acked action successful !!!"
        self.logger.info(msg)

    def verify_query_cpu_freqs_from_vm(self):
        except_content = None
        msg = "begin test query cpu freqs from vm ..."
        self.logger.info(msg)
        try:
            self.run_test_pre()
            self.check_query_cpu_freqs_command()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        msg = "test query cpu freqs from vm successful !!!"
        self.logger.info(msg)

    def verify_query_cpu_capability(self):
        except_content = None
        msg = "begin test query cpu capability ..."
        self.logger.info(msg)
        try:
            self.run_test_pre()
            self.check_cpu_capability_on_vm()
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        msg = "test query cpu capability successful !!!"
        self.logger.info(msg)

    def verify_power_driver(self):
        expected_drv = 'acpi-cpufreq'
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv)
        self.verify(power_drv == expected_drv, msg)

    def preset_test_environment(self):
        self.is_mgr_on = None
        self.ext_con = {}
        # modprobe msr module to let the application can get the CPU HW info
        self.d_a_con('modprobe msr')
        self.d_a_con('cpupower frequency-set -g userspace')
        self.dut.init_core_list_uncached_linux()
        # check if cpu support bpf feature
        self.base_freqs_info = self.get_all_cpu_attrs()
        # boot up vm
        self.start_vm()
        # init binary
        self.init_vm_power_mgr()
        self.init_guest_mgr()

    #
    # Test cases.
    #

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
        self.vm_dut.kill_all()
        self.dut.kill_all()

    def test_policy_command_acked_action(self):
        """
        Check VM can send power policy command to host and get acked
        """
        self.verify_policy_command_acked_action()

    def test_query_cpu_freqs_from_vm(self):
        """
        Query Host CPU frequency list from VM
        """
        self.verify_query_cpu_freqs_from_vm()

    def test_query_cpu_capability(self):
        """
        Query CPU capability from VM
        """
        self.verify_query_cpu_capability()
