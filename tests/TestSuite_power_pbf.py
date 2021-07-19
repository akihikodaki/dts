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

import os
import time
import random
import json
import re
import shutil
import traceback
from collections import Counter
from pprint import pformat

# import dts libs
from settings import load_global_setting
from settings import HOST_BUILD_TYPE_SETTING
from test_case import TestCase
from exception import VerifyFailure
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
        suiteName = self.suite_name
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
        time.sleep(2)
        return outputs

    def d_con(self, cmds):
        return self.execute_cmds(cmds, con_name='dut')

    def d_a_con(self, cmds):
        return self.execute_cmds(cmds, con_name='dut_alt')

    def get_cores_mask(self, config='all'):
        sockets = [self.dut.get_numa_id(index) for index in self.dut_ports]
        socket_count = Counter(sockets)
        port_socket = list(socket_count.keys())[0] if len(socket_count) == 1 else -1
        mask = create_mask(self.dut.get_core_list(config, socket=port_socket))
        return mask

    def prepare_binary(self, name):
        example_dir = "examples/" + name
        out = self.dut.build_dpdk_apps('./' + example_dir)
        return os.path.join(self.target_dir,
                            self.dut.apps_name[os.path.basename(name)])

    def create_powermonitor_folder(self):
        cmd = 'mkdir -p {0}; chmod 777 {0}'.format('/tmp/powermonitor')
        self.d_con(cmd)

    def init_test_binary_file(self):
        self.create_powermonitor_folder()
        # open debug SW
        SW = "CONFIG_RTE_LIBRTE_POWER_DEBUG"
        if 'meson' == load_global_setting(HOST_BUILD_TYPE_SETTING):
            self.dut.set_build_options({SW[7:]: 'y'})
        else:
            cmd = "sed -i -e 's/{0}=n$/{0}=y/' {1}/config/common_base".format(
                SW, self.target_dir)
            self.d_a_con(cmd)
        self.dut.build_install_dpdk(self.target)
        # set up vm power management binary process setting
        self.vm_power_mgr = self.prepare_binary('vm_power_manager')
        # set up distributor binary process setting
        self.distributor = self.prepare_binary('distributor')
        self.is_mgr_on = self.is_distributor_on = None

    def start_vm_power_mgr(self):
        if self.is_mgr_on:
            return
        bin_file = os.sep.join([self.target_dir, ''])
        config = "2S/23C/1T"
        option = '-v -c {0} -n {1} --file-prefix=vmpower --no-pci'.format(
            self.get_cores_mask(config),
            self.memory_channels)
        prompt = 'vmpower>'
        cmd = [' '.join([self.vm_power_mgr, option]), prompt, 30]
        output = self.d_con(cmd)
        self.is_mgr_on = True

        return output

    def close_vm_power_mgr(self):
        if not self.is_mgr_on:
            return
        output = self.d_con('quit')
        self.is_mgr_on = False
        return output

    def start_distributor(self, high_core_num=1):
        if self.is_distributor_on:
            return
        cores_mask, high_freq_cores = self.get_high_freq_core_mask(
            high_core_num)
        option = '-v -c {0} -n {1} -- -p 0x1'.format(
            cores_mask, self.memory_channels)
        prompt = 'Distributor thread'
        cmd = [' '.join([self.distributor, option]), prompt, 30]
        output = self.d_con(cmd)
        self.is_distributor_on = True
        return high_freq_cores, output

    def close_distributor(self):
        if not self.is_distributor_on:
            return
        cmd = "^C"
        self.d_con(cmd)
        self.is_distributor_on = False

    def __preset_single_core_json_cmd(self, core_index, unit, name):
        command = {
            "instruction": {
                # name of the vm or host
                "name":         name,
                "command":      "power",
                "unit":         unit, }}
        # generate json data file and scp it to dut target source code folder
        json_name = 'command_{}.json'.format(core_index)
        json_file = os.sep.join([self.output_path, json_name])
        with open(json_file, 'w') as fp:
            json.dump(command, fp, indent=4, separators=(',', ': '),
                      sort_keys=True)
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
        self.d_a_con(';'.join(cmds))

    def get_core_cur_freq(self, core_index):
        cpu_attr = r'/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_cur_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_con(cmd)
        return int(output)

    def get_core_scaling_max_freq(self, core_index):
        cpu_attr = r'/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_max_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_con(cmd)
        return int(output)

    def get_core_scaling_min_freq(self, core_index):
        cpu_attr = r'/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_min_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_con(cmd)
        return int(output)

    def get_core_scaling_base_freq(self, core_index):
        cpu_attr = r'/sys/devices/system/cpu/cpu{0}/cpufreq/base_frequency'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_con(cmd)
        return int(output)

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

    def get_sys_power_driver(self):
        drv_file = r"/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con('cat ' + drv_file)
        if not output:
            msg = 'unknown power driver'
            self.verify(False, msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    def get_all_cpu_attrs(self):
        ''' get all cpus' base_frequency value '''
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
        for core_index, value in list(cpu_info.items()):
            base_frequency = value.get('base_frequency')
            base_freqs_info.setdefault(base_frequency, []).append(core_index)
        base_freqs = list(base_freqs_info.keys())
        # cpu should have high priority core and normal core
        # high priority core frequency is higher than normal core frequency
        if len(base_freqs) <= 1 or \
           not all([len(value) for value in list(base_freqs_info.values())]):
            msg = 'current cpu has no high priority core'
            raise Exception(msg)

        return cpu_info, base_freqs_info

    def get_normal_cores_index(self):
        ''' get one random normal core index, ignore core 0 '''
        normal_freq = min(self.base_freqs_info.keys())
        cores_index = self.base_freqs_info[normal_freq][1:] \
            if self.base_freqs_info[normal_freq][0] == 0 else \
            self.base_freqs_info[normal_freq]
        return cores_index

    def get_high_freq_cores_index(self, number=1):
        ''' get one random high frequency core index, ignore core 0 '''
        high_freq = max(self.base_freqs_info.keys())
        cores_index = self.base_freqs_info[high_freq][-number:]
        return cores_index

    def get_high_freq_core_mask(self, number=1, min_cores=5):
        index_list = []
        # get high frequency core first
        cores_index = self.get_high_freq_cores_index(number)
        [index_list.append(core_index) for core_index in cores_index]
        high_freq_cores = index_list[:]
        # get normal cores to make sure minimum cores are enough
        cores_index = self.get_normal_cores_index()
        for core_index in cores_index:
            if core_index in index_list:
                continue
            index_list.append(core_index)
            if len(index_list) >= min_cores:
                break
        # create core mask
        cores_mask = create_mask(index_list)
        return cores_mask, high_freq_cores

    def parse_vm_power_cores_freq(self, output):
        ''' get vm power management cores frequency '''
        pat_begin = (
            'POWER: power_set_governor: Power management '
            'governor of lcore (\\d+) is already performance')
        pat_begin2 = (
            "Power management governor of lcore (\d+) "
            "has been set to 'performance' successfully")
        pat_end = \
            'POWER: Initialized successfully for lcore (\\d+) power management'
        pat_freq = (
            'POWER: power_get_available_freqs: '
            'sys min (\\d+), sys max (\\d+), base_max (\\d+)')
        cores_info = {}
        flag = False
        core_id = None
        for line in output.splitlines():
            # if core output begin message
            result = re.findall(pat_begin, line)
            result2 = re.findall(pat_begin2, line)
            if result or result2:
                if result:
                    core_id = int(result[0])
                elif result2:
                    core_id = int(result2[0])
                flag = True
            if flag:
                result = re.findall(pat_freq, line)
                if result and len(result[0]) == 3:
                    cores_info[core_id] = {}
                    cores_info[core_id]['cpuinfo_min_freq'] = result[0][0]
                    cores_info[core_id]['cpuinfo_max_freq'] = result[0][1]
                    cores_info[core_id]['base_frequency'] = result[0][2]
            # if core output last message
            result = re.findall(pat_end, line)
            if result:
                core_id = None
                flag = False
        return cores_info

    def check_core_freq_for_unit(self, unit, core_index, ref_freq_name):
        msg = ("begin verify core <{0}> command <{1}> action ...").format(
            core_index, unit)
        self.logger.info(msg)
        self.send_json_command(core_index, unit)
        expected_freq = self.cpu_info[core_index].get(ref_freq_name)
        max_freq = self.get_core_scaling_max_freq(core_index)
        min_freq = self.get_core_scaling_min_freq(core_index)
        msg = 'max freq<{0}>/min_freq<{1}>/expected freq<{2}> are not the same'
        self.verify(
            max_freq == min_freq and max_freq == expected_freq,
            msg.format(max_freq, min_freq, expected_freq))
        msg = ("core <{0}> command <{1}> action is ok").format(
            core_index, unit)
        self.logger.info(msg)

    def verify_high_priority_core(self):
        # run vm power binary file
        output = self.start_vm_power_mgr()
        self.close_vm_power_mgr()
        # parse output message
        cores_info = self.parse_vm_power_cores_freq(output)
        # get high priority core and normal core
        base_freqs_info = {}
        for core_index, value in list(cores_info.items()):
            base_frequency = value.get('base_frequency')
            base_freqs_info.setdefault(base_frequency, []).append(core_index)
        base_freqs = list(base_freqs_info.keys())
        # cpu should have high priority core and normal core
        # high priority core frequency is higher than normal core frequency
        if len(base_freqs) <= 1 or \
           not all([len(value) for value in list(base_freqs_info.values())]):
            msg = 'current cpu has no high priority core'
            raise Exception(msg)

    def verify_high_priority_core_min_max_freq(self):
        '''
        random select one high priority core to run testing
        Send different command to power sample:
        Command Steps:
            ENABLE_TURBO
            SCALE_MAX
            SCALE_DOWN
            SCALE_MIN
        Check the CPU frequency is changed accordingly in this list
        '''
        except_content = None
        try:
            self.start_vm_power_mgr()
            # random select one high priority core to run testing
            core_index = self.get_high_freq_cores_index()[0]
            # Enable turbo Boost for this core
            self.send_json_command(core_index, 'ENABLE_TURBO')
            # these test items sequence can't changed
            test_items = [
                # Scale frequency of this core to maximum
                ["SCALE_MAX", core_index, 'cpuinfo_max_freq'],
                # Scale down frequency of this core
                ["SCALE_DOWN", core_index, 'base_frequency'],
                # Scale frequency of this core to minimum
                ["SCALE_MIN", core_index, 'cpuinfo_min_freq'],
            ]
            # test cpu core frequency change with unit command
            for test_item in test_items:
                self.check_core_freq_for_unit(*test_item)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_vm_power_mgr()

        if except_content:
            raise VerifyFailure(except_content)

    def verify_high_priority_core_turbo_status(self):
        '''
        Send different command to power sample:
        Command Steps:
            ENABLE_TURBO
            SCALE_MAX
            ENABLE_TURBO
        Check the CPU frequency is changed accordingly in this list
        '''
        except_content = None
        try:
            self.start_vm_power_mgr()
            # random select one high priority core to run testing
            core_index = self.get_high_freq_cores_index()[0]
            # Enable Turbo Boost for this core
            self.send_json_command(core_index, 'ENABLE_TURBO')
            # Scale frequency of this core to maximum
            test_items = [
                ["SCALE_MAX", core_index, 'cpuinfo_max_freq'],
                ["DISABLE_TURBO", core_index, 'base_frequency'], ]
            # test cpu core frequency change with unit command
            for test_item in test_items:
                self.check_core_freq_for_unit(*test_item)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_vm_power_mgr()

        if except_content:
            raise VerifyFailure(except_content)

    def verify_distributor_high_priority_core(self):
        '''
        check distributor example use high priority core as distribute core
        '''
        except_content = None
        try:
            high_freq_cores, output = self.start_distributor()
            self.close_distributor()
            expected_str = "Distributor on priority core {0}".format(
                high_freq_cores[0])
            self.verify(expected_str in output,
                        "'{}' not display".format(expected_str))
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_distributor()

        if except_content:
            raise VerifyFailure(except_content)

    def verify_distributor_high_priority_core_txrx(self):
        '''
        check distributor sample will use high priority core for
        distribute core and rx/tx core
        '''
        except_content = None
        try:
            high_freq_cores, output = self.start_distributor(3)
            self.close_distributor()
            # check the high priority core are assigned as rx core in log
            pat = 'Core (\d+) doing packet RX.'
            result = re.findall(pat, output, re.M)
            if len(result) == 1:
                core_index = int(result[0])
            else:
                msg = "haven't catch expected RX core"
                self.verify(False, msg)
            msg = "No high frequency core doing packet RX"
            self.verify(core_index in high_freq_cores, msg)
            # Check the high priority core are assigned as tx core in log
            pat = 'Core (\d+) doing packet TX.'
            result = re.findall(pat, output, re.M)
            if len(result) == 1:
                core_index = int(result[0])
            else:
                msg = "haven't catch expected TX core"
                self.verify(False, msg)
            msg = "No high frequency core doing packet TX"
            self.verify(core_index in high_freq_cores, msg)
            # check the high priority core is assigned as distributor core in
            # log
            pat = r'Core (\d+) acting as distributor core.'
            result = re.findall(pat, output, re.M)
            if len(result) == 1:
                core_index = int(result[0])
            else:
                msg = "haven't catch expected distributor core"
                self.verify(False, msg)
            msg = "No high frequency core acting as distributor core"
            self.verify(core_index in high_freq_cores, msg)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_distributor()

        if except_content:
            raise VerifyFailure(except_content)

    def verify_pbf_supported(self):
        if self.is_support_pbf:
            return
        msg = "dut cpu doesn't support power pbf feature"
        raise Exception(msg)

    def verify_power_driver(self):
        expected_drv = 'intel_pstate'
        power_drv = self.get_sys_power_driver()
        msg = "power pbf should work with {} driver".format(expected_drv)
        self.verify(power_drv == expected_drv, msg)
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run before each test suite
        """
        self.verify_power_driver()
        # get ports information
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        # get dut node cores information
        self.d_a_con('modprobe msr')
        self.dut.init_core_list_uncached_linux()
        # check if cpu support bpf feature
        self.verify_pbf_supported()
        self.cpu_info, self.base_freqs_info = self.get_all_cpu_attrs()
        self.logger.info(pformat(self.cpu_info))
        self.logger.info(pformat(self.base_freqs_info))
        self.memory_channels = self.dut.get_memory_channels()
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
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass

    def test_high_priority_core(self):
        '''
        check high priority core can be recognized by power lib
        '''
        self.verify_high_priority_core()

    def test_high_priority_core_min_max_freq(self):
        '''
        set cpu min and max frequency test for the high priority core
        '''
        self.verify_high_priority_core_min_max_freq()

    def test_high_priority_core_turbo_status(self):
        '''
        check "DISABLE_TURBO" Action when core is in turbo status for
        high priority core
        '''
        self.verify_high_priority_core_turbo_status()

    def test_distributor_high_priority_core(self):
        '''
        check distributor sample use high priority core as distribute core
        '''
        self.verify_distributor_high_priority_core()

    def test_distributor_high_priority_core_txrx(self):
        '''
        check distributor sample will use high priority core for distribute
        core and rx/tx core
        '''
        self.verify_distributor_high_priority_core_txrx()
