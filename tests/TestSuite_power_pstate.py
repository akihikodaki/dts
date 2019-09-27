# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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

import os
import time
import random
import json
import shutil
from collections import Counter
from pprint import pformat

# import dts libs
from test_case import TestCase
from utils import create_mask


class TestPowerPbf(TestCase):

    def timestamp(self):
        curTime = time.localtime()
        timestamp = "%04d%02d%02d_%02d-%02d-%02d" % (
            curTime.tm_year, curTime.tm_mon, curTime.tm_mday,
            curTime.tm_hour, curTime.tm_min, curTime.tm_sec)
        return timestamp

    @property
    def target_dir(self):
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    @property
    def output_path(self):
        suiteName = self.__class__.__name__[4:].lower()
        if self.logger.log_path.startswith(os.sep):
            output_path = os.path.join(self.logger.log_path, suiteName)
        else:
            cur_path = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))
            output_path = os.path.join(
                cur_path, self.logger.log_path, suiteName)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        return output_path

    def get_console(self, name):
        if name == 'dut':
            console = self.dut.send_expect
            msg_pipe = self.dut.get_session_output
        elif name == 'dut_alt':
            console = self.dut.alt_session.send_expect
            msg_pipe = self.dut.alt_session.session.get_output_all
        return console, msg_pipe

    def execute_cmds(self, cmds, con_name='dut'):
        console, msg_pipe = self.get_console(con_name)
        if len(cmds) == 0:
            return
        if isinstance(cmds, (str, unicode)):
            cmds = [cmds, '# ', 5]
        if not isinstance(cmds[0], list):
            cmds = [cmds]
        outputs = [] if len(cmds) > 1 else ''
        for item in cmds:
            expected_items = item[1]
            if expected_items and isinstance(expected_items, (list, tuple)):
                check_output = True
                expected_str = expected_items[0] or '# '
            else:
                check_output = False
                expected_str = expected_items or '# '

            try:
                if len(item) == 3:
                    timeout = int(item[2])
                    output = console(item[0], expected_str, timeout)
                    output = msg_pipe() if not output else output
                else:
                    # timeout = 5
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

    def d_console(self, cmds):
        return self.execute_cmds(cmds, con_name='dut')

    def d_a_console(self, cmds):
        return self.execute_cmds(cmds, con_name='dut_alt')

    def get_cores_mask(self, config='all'):
        sockets = [self.dut.get_numa_id(index) for index in self.dut_ports]
        socket_count = Counter(sockets)
        port_socket = socket_count.keys()[0] if len(socket_count) == 1 else -1
        mask = create_mask(self.dut.get_core_list(config, socket=port_socket))
        return mask

    def create_powermonitor_folder(self):
        cmd = 'mkdir -p {0}; chmod 777 {0}'.format('/tmp/powermonitor')
        self.d_console(cmd)

    def prepare_binary(self, name):
        example_dir = "examples/" + name
        out = self.dut.build_dpdk_apps('./' + example_dir)
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        binary_dir = os.path.join(self.target_dir, example_dir, 'build')
        cmd = ["ls -F {0} | grep '*'".format(binary_dir), '# ', 5]
        exec_file = self.d_a_console(cmd)
        binary_file = os.path.join(binary_dir, exec_file[:-1])
        return binary_file

    def init_test_binary_file(self):
        self.create_powermonitor_folder()
        # set up vm power binary process setting
        self.vm_power_mgr = self.prepare_binary('vm_power_manager')

    def start_vm_power_mgr(self):
        config = "1S/4C/1T"
        eal_option = '-c {0} -n {1} --file-prefix=vmpower --no-pci'.format(
            self.get_cores_mask(config),
            self.memory_channels)
        prompt = 'vmpower>'
        cmd = [' '.join([self.vm_power_mgr, eal_option]), prompt, 30]
        output = self.d_console(cmd)
        return output

    def close_vm_power_mgr(self):
        output = self.d_console('quit')
        return output

    def __preset_single_core_json_cmd(self, core_index, unit, name):
        command = {
            "instruction": {
                # name of the vm or host
                "name": name,
                "command": "power",
                "unit": unit, }}
        # generate json data file and scp it to dut target source code folder
        json_name = 'command_{}.json'.format(core_index)
        json_file = os.sep.join([self.output_path, json_name])
        with open(json_file, 'w') as fp:
            json.dump(command, fp, indent=4, separators=(',', ': '),
                      encoding="utf-8", sort_keys=True)
            fp.write(os.linesep)
        self.dut.session.copy_file_to(json_file, self.target_dir)
        # save a backup json file to retrace test command
        backup_file = json_file + self.timestamp()
        shutil.move(json_file, backup_file)
        # send action JSON file to vm_power_mgr's fifo channel
        cmd = 'cat {0}/{2} > /tmp/powermonitor/fifo{1}'.format(
            self.target_dir, core_index, json_name)

        return cmd

    def send_json_command(self, cores, unit, name='policy1'):
        if type(cores) == int:
            _cores = [cores]
        elif type(cores) == list:
            _cores = cores[:]
        else:
            msg = 'not support input cores type'
            self.verify(False, msg)

        cmds = []
        for core_index in _cores:
            cmds.append(
                self.__preset_single_core_json_cmd(core_index, unit, name))
        self.d_a_console(';'.join(cmds))

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_console('cat ' + drv_file)
        if not output:
            msg = 'unknown power driver'
            self.verify(False, msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    @property
    def is_hyper_threading(self):
        cpu_index = self.cpu_info.keys()[-1]
        core_num = self.cpu_info[cpu_index].get('core')
        return (cpu_index + 1) / 2 == (core_num + 1)

    def get_core_scaling_max_freq(self, core_index):
        cpu_attr = '/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_max_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_console(cmd)
        return int(output)

    def get_core_scaling_min_freq(self, core_index):
        cpu_attr = '/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_min_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_console(cmd)
        return int(output)

    def get_no_turbo_max(self):
        cmd = 'rdmsr -p 1 0x0CE -f 15:8 -d'
        output = self.d_a_console(cmd)
        freq = output.strip() + '00000'
        return int(freq)

    def get_all_cpu_attrs(self):
        ''' get all cpus' attribute '''
        key_values = ['cpuinfo_max_freq',
                      'cpuinfo_min_freq']
        freq = '/sys/devices/system/cpu/cpu{0}/cpufreq/{1}'.format
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
            output = self.d_a_console(';'.join(cmds))
            freqs = [int(item) for item in output.splitlines()]
            for index, cpu_id in enumerate(sorted(cpu_info.keys())):
                cpu_info[cpu_id][key_value] = freqs[index]

        return cpu_info

    def check_core_freq_for_unit(self, unit, core_index, ref_freq_name):
        ''' check the core frequency '''
        msg = ("begin verify core <{0}> command <{1}> action ...").format(
            core_index, unit)
        self.logger.info(msg)
        self.send_json_command(core_index, unit)
        expected_freq = self.get_no_turbo_max() \
            if ref_freq_name == 'no_turbo_max' else \
            self.cpu_info[core_index].get(ref_freq_name)
        max_freq = self.get_core_scaling_max_freq(core_index)
        min_freq = self.get_core_scaling_min_freq(core_index)
        msg = 'max freq<{0}>/min_freq<{1}>/expected freq<{2}> are not the same'
        self.verify(
            max_freq == min_freq and max_freq == expected_freq,
            msg.format(max_freq, min_freq, expected_freq))
        msg = ("core <{0}> command <{1}> action is ok").format(
            core_index, unit)
        self.logger.info(msg)

    def verify_power_driver(self):
        power_drv = self.get_sys_power_driver()
        msg = "power pstate should work with intel_pstate driver"
        self.verify(power_drv == 'intel_pstate', msg)

    def verify_hyper_threading(self):
        msg = "power pstate should work under hyper threading close status"
        self.verify(not self.is_hyper_threading, msg)

    def verify_pstate_basic_action(self):
        '''
        random select cpu core to run testing
        Send different command to power sample:
        Command Steps:
            ENABLE_TURBO
            SCALE_MIN
            SCALE_MAX
            DISABLE_TURBO
            SCALE_UP
            SCALE_DOWN
        Check the CPU frequency is changed accordingly in this list
        '''
        try:
            self.start_vm_power_mgr()
            # select one core to run testing
            core_index = 1
            # Enable turbo Boost for this core
            self.send_json_command(core_index, 'ENABLE_TURBO')
            # these test items sequence can't changed
            test_items = [
                # Scale frequency of this core to minimum
                ["SCALE_MIN", core_index, 'cpuinfo_min_freq'],
                # Scale frequency of this core to maximum
                ["SCALE_MAX", core_index, 'cpuinfo_max_freq'],
                ["DISABLE_TURBO", core_index, 'no_turbo_max'],
                ["ENABLE_TURBO", core_index, 'no_turbo_max'],
                ["SCALE_UP", core_index, 'cpuinfo_max_freq'],
                ["SCALE_DOWN", core_index, 'no_turbo_max'], ]
            # test cpu core frequency change with unit command
            for test_item in test_items:
                self.check_core_freq_for_unit(*test_item)
            self.close_vm_power_mgr()
        except Exception as e:
            self.close_vm_power_mgr()
            raise Exception(e)
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run before each test suite
        """
        # get ports information
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.d_a_console('modprobe msr')
        # get dut node cores information
        self.dut.init_core_list_uncached_linux()
        self.cpu_info = self.get_all_cpu_attrs()
        self.logger.info(pformat(self.cpu_info))
        self.memory_channels = self.dut.get_memory_channels()
        self.verify_power_driver()
        self.verify_hyper_threading()
        self.init_test_binary_file()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass

    def test_pstate_basic_action(self):
        '''
        test pstate lib basic action based on directly power command
        '''
        self.verify_pstate_basic_action()
