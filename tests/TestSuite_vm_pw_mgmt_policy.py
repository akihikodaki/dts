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
virtual power manager policy (traffic/time) test suite.
"""
import os
import re
import time
import textwrap
import random
import traceback
from itertools import product
from datetime import datetime, timedelta
from copy import deepcopy
from pprint import pformat

from utils import create_mask as dts_create_mask
from test_case import TestCase
from pmd_output import PmdOutput
from qemu_libvirt import LibvirtKvm
from pktgen import TRANSMIT_CONT
from exception import VerifyFailure
from packet import Packet


class TestVmPwMgmtPolicy(TestCase):
    # policy mode
    TIME = 'TIME'
    TRAFFIC = 'TRAFFIC'
    # temporary file directory
    output_path = '/tmp'

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def get_cores_mask(self, config='all', crb=None):
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

    def config_stream(self, stm_names=None):
        dmac = self.vm_dut.get_mac_address(0)
        # set streams for traffic
        pkt_configs = {
            'UDP_1': {
                'type': 'UDP',
                'pkt_layers': {'ether': {'dst': dmac, }, }, },
        }
        # create packet for send
        streams = []
        for stm_name in stm_names:
            if stm_name not in list(pkt_configs.keys()):
                continue
            values = pkt_configs[stm_name]
            pkt_type = values.get('type')
            pkt_layers = values.get('pkt_layers')
            pkt = Packet(pkt_type=pkt_type)
            for layer in list(pkt_layers.keys()):
                pkt.config_layer(layer, pkt_layers[layer])
            streams.append(pkt.pktgen.pkt)
            self.logger.debug(pkt.pktgen.pkt.command())

        return streams

    def add_stream_to_pktgen(self, txport, rxport, send_pkt, option):
        stream_ids = []
        for pkt in send_pkt:
            _option = deepcopy(option)
            _option['pcap'] = pkt
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def send_packets_by_pktgen(self, option):
        txport = option.get('tx_intf')
        rxport = option.get('rx_intf')
        rate_percent = option.get('rate_percent', float(100))
        send_pkt = option.get('stream') or []
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        stream_option = {
            'stream_config': {
                'txmode': {},
                'transmit_mode': TRANSMIT_CONT,
                'rate': rate_percent, }
        }
        stream_ids = self.add_stream_to_pktgen(
            txport, rxport, send_pkt, stream_option)
        # run traffic options
        traffic_opt = option.get('traffic_opt')
        # run pktgen traffic
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)

        return result

    def get_rate_percent(self, pps):
        frame_size = 64
        full_pps = self.wirespeed(self.nic, frame_size, 1) * 1000000.0
        rate_percent = round((100 * float(pps) / float(full_pps)), 2)
        return rate_percent

    def run_traffic(self, option):
        dut_port = self.dut_ports[self.used_port]
        tester_tx_port_id = self.tester.get_local_port(dut_port)
        tester_rx_port_id = self.tester.get_local_port(dut_port)
        stm_type = option.get('stm_types')
        pps = option.get('pps')
        rate = self.get_rate_percent(pps)
        duration = option.get('duration', None) or 15
        ports_topo = {
            'tx_intf': tester_tx_port_id,
            'rx_intf': tester_rx_port_id,
            'stream': self.config_stream(stm_type),
            'rate_percent': rate,
            'traffic_opt': {
                'method': 'throughput',
                'callback': self.query_cpu_freq,
                'interval': duration - 2,
                'duration': duration,
            }}
        # begin traffic checking
        result = self.send_packets_by_pktgen(ports_topo)

        return result

    def bind_ports_to_sys(self):
        for port in self.dut.ports_info:
            netdev = port.get('port')
            if not netdev:
                continue
            cur_drv = netdev.get_nic_driver()
            netdev.bind_driver(netdev.default_driver)
        else:
            cur_drv = 'igb_uio'
        return cur_drv

    def bind_ports_to_dpdk(self, driver):
        if not driver:
            return
        for port in self.dut.ports_info:
            netdev = port.get('port')
            if not netdev:
                continue
            cur_drv = netdev.get_nic_driver()
            if cur_drv == driver:
                continue
            netdev.bind_driver(driver)

    def init_vms_params(self):
        self.vm = self.vcpu_map = self.vm_dut = self.guest_session = \
            self.is_guest_on = self.is_vm_on = self.is_vf_set = None
        # vm config
        self.vm_name = 'vm0'
        self.vm_max_ch = 8
        self.vm_log_dir = '/tmp/powermonitor'
        self.create_powermonitor_folder()

    def create_powermonitor_folder(self):
        # create temporary folder for power monitor
        cmd = 'mkdir -p {0}; chmod 777 {0}'.format(self.vm_log_dir)
        self.d_a_con(cmd)

    def create_vf(self, driver='default'):
        self.dut.generate_sriov_vfs_by_port(self.used_port, 1, driver=driver)
        self.is_vf_set = True
        sriov_vfs_port = self.dut.ports_info[self.used_port]['vfs_port']
        return sriov_vfs_port[0].pci

    def destroy_vf(self):
        if not self.is_vf_set:
            return
        self.dut.destroy_sriov_vfs_by_port(self.used_port)
        self.is_vf_set = False
        port = self.dut.ports_info[self.used_port]['port']
        port.bind_driver()

    def add_nic_device(self, pci_addr, vm_inst):
        vm_params = {
            'driver': 'pci-assign',
            'driver': 'vfio',
            'opt_host': pci_addr,
            'guestpci':  '0000:00:07.0'}
        vm_inst.set_vm_device(**vm_params)

    def start_vm(self):
        # set vm initialize parameters
        self.init_vms_params()
        # start vm
        self.vm = LibvirtKvm(self.dut, self.vm_name, self.suite_name)
        # pass vf to virtual machine
        pci_addr = self.create_vf()
        self.add_nic_device(pci_addr, self.vm)
        # add channel
        ch_name = 'virtio.serial.port.poweragent.{0}'
        vm_path = os.path.join(self.vm_log_dir, '{0}.{1}')
        for cnt in range(self.vm_max_ch):
            channel = {
                'path': vm_path.format(self.vm_name, cnt),
                'name': ch_name.format(cnt)}
            self.vm.add_vm_virtio_serial_channel(**channel)
        # set vm default driver
        self.vm.def_driver = 'igb_uio'
        # boot up vm
        self.vm_dut = self.vm.start()
        self.is_vm_on = True
        self.verify(self.vm_dut, "create vm_dut fail !")
        self.add_console(self.vm_dut.session)
        # get virtual machine cpu cores
        _vcpu_map = self.vm.get_vm_cpu()
        self.vcpu_map = [int(item) for item  in _vcpu_map]

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
        # destroy vf
        if self.is_vf_set:
            self.destroy_vf()

    def init_vm_power_mgr(self):
        self.vm_power_mgr = self.prepare_binary('vm_power_manager')

    def start_vm_power_mgr(self):
        eal_option = (
            '-v '
            '-c {core_mask} '
            '-n {mem_channel} ').format(**{
                'core_mask': self.get_cores_mask("1S/3C/1T"),
                'mem_channel': self.dut.get_memory_channels(), })
        prompt = 'vmpower>'
        cmd = [' '.join([self.vm_power_mgr, eal_option]), prompt, 30]
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

    def init_guest_mgr(self):
        name = 'vm_power_manager/guest_cli'
        self.guest_cli = self.prepare_binary(name, host_crb=self.vm_dut)
        self.guest_con_name = \
            '_'.join([self.vm_dut.NAME, name.replace('/', '-')])
        self.guest_session = self.vm_dut.create_session(self.guest_con_name)
        self.add_console(self.guest_session)

    def start_guest_mgr(self, cmd_option):
        prompt = r"vmpower\(guest\)>"
        option = (
            '-v '
            '-c {core_mask} '
            '-n {memory_channel} '
            '--file-prefix={file_prefix} '
            '-- ').format(**{
                'core_mask': '0xff',
                'memory_channel': self.vm_dut.get_memory_channels(),
                'file_prefix': 'vmpower2',
            }) + cmd_option
        guest_cmd = ' '.join([self.guest_cli, option])
        self.vm_g_con([guest_cmd, prompt, 120])
        self.is_guest_on = True

    def guest_send_policy(self):
        self.vm_g_con(['send_policy now', r"vmpower\(guest\)>", 20])
        # it would be a problem measuring less than 500ms after sending
        # policy, so wait 2 second here.
        time.sleep(2)

    def guest_set_vm_turbo_status(self, vcpu, status):
        vcpu_index = self.vcpu_map.index(self.check_core)
        cmd = ["set_cpu_freq %d %s" % (vcpu_index, status),
               "vmpower\(guest\)>", 5]
        output = self.vm_g_con(cmd)
        self.verify(
            'ACK received for message sent to host'.lower() in output.lower(),
            'vm guest failed to send message host')

    def close_guest_mgr(self):
        if not self.is_guest_on:
            return
        self.vm_g_con("quit")
        self.is_guest_on = False

    def init_vm_testpmd(self):
        self.vm_testpmd = PmdOutput(self.vm_dut)

    def start_vm_testpmd(self):
        eal_param = (
            '-v '
            '-m {memsize} '
            '--file-prefix={file-prefix}').format(**{
                'file-prefix': 'vmpower1',
                'memsize': 1024, })
        self.vm_testpmd.start_testpmd(
            "Default",
            param='--port-topology=loop',
            eal_param=eal_param)
        self.is_pmd_on = True

    def set_vm_testpmd(self):
        cmds = [
            'set fwd mac',
            'set promisc all on',
            'port start all',
            'start']
        self.vm_testpmd.execute_cmd(cmds)

    def close_vm_testpmd(self):
        if not self.is_pmd_on:
            return
        self.vm_testpmd.quit()
        self.is_pmd_on = False

    def query_cpu_freq(self):
        cmd = ("cat "
            "/sys/devices/system/cpu/cpu{}/cpufreq/cpuinfo_cur_freq").format(
            self.check_core)
        output = self.d_a_con(cmd)
        self.cur_cpu_freq = 0 if not output else int(output.splitlines()[0])

    def set_desired_time(self, time_stage):
        if not time_stage:
            return None * 2
        # only select one random time stage
        random_index = random.randint(0, len(time_stage) - 1)
        timestamp = time_stage[random_index]
        ori_sys_time = datetime.now()
        msg = "dut system original time is {0}".format(ori_sys_time)
        self.logger.debug(msg)
        # set system time to a desired time for policy
        msg = "set timestamp {0}".format(timestamp)
        self.logger.debug(msg)
        date_tool = "date"
        cmd = ';'.join([
            "{0}",
            "{0} -s '{1}'",
            "hwclock -w"]).format(date_tool, timestamp)
        self.d_a_con([cmd, '# ', 20])
        cmd = "{0} '+%H:00'".format(date_tool)
        output = self.d_a_con(cmd)
        msg = "desired time fails to set" \
              if output.strip() != timestamp \
              else "desired time set successful"
        self.logger.info(msg)
        # get begin time stamp
        pre_time = datetime.now()
        # when dut/tester are on the same node, separate into two timestamp
        return pre_time, ori_sys_time

    def restore_system_time(self, pre_time, ori_sys_time):
        if not ori_sys_time:
            return
        date_tool = "date"
        cur_time = datetime.now()
        interval = (cur_time - pre_time).seconds
        timestamp = ori_sys_time + timedelta(seconds=interval)
        FMT = '%Y-%m-%d %H:%M:%S'
        real_time = timestamp.strftime(FMT)
        cmd = ';'.join([
            "{0}",
            "{0} -s '{1}'",
            "hwclock -w",
            "{0}", ]).format(date_tool, real_time)
        self.d_a_con([cmd, '# ', 20])

    def preset_core_freq(self):
        info = self.cpu_info.get(self.check_core, {})
        freq = info.get('scaling_available_frequencies')[-3]
        cmd = ("cpupower -c all frequency-set -f {} "
               "> /dev/null 2>&1").format(freq)
        self.d_a_con(cmd)

    def get_all_cpu_attrs(self):
        ''' get all cpus attribute '''
        key_values = [
            'scaling_max_freq',
            'scaling_available_frequencies',
            'scaling_min_freq']
        freq = '/sys/devices/system/cpu/cpu{0}/cpufreq/{1}'.format
        cpu_topos = self.dut.get_all_cores()
        cpu_info = {}
        for cpu_topo in cpu_topos:
            cpu_id = int(cpu_topo.get('thread'))
            cpu_info[cpu_id] = {
                'socket': cpu_topo.get('socket'),
                'core': cpu_topo.get('core')}

        for key_value in key_values:
            cmds = []
            for cpu_id in sorted(cpu_info.keys()):
                cmds.append('cat {0}'.format(freq(cpu_id, key_value)))
            output = self.d_a_con(';'.join(cmds))
            freqs = [int(item) for item in output.splitlines()] \
                if key_value != 'scaling_available_frequencies' else \
                    [item for item in output.splitlines()]
            for index, cpu_id in enumerate(sorted(cpu_info.keys())):
                if key_value == 'scaling_available_frequencies':
                    cpu_info[cpu_id][key_value] = freqs[index]
                cpu_info[cpu_id][key_value] = \
                    [int(item) for item in sorted(freqs[index].split())] \
                    if key_value == 'scaling_available_frequencies' else \
                    freqs[index]

        return cpu_info

    def convert_to_values(self, output):
        pdata_s = "^\d+$"
        ret = re.match(pdata_s, output)
        if ret:
            return int(output)
        pdata_m = "(\d+ )+"
        ret = re.match(pdata_m, output)
        if ret:
            return [int(item) for item in output.split()]
        pdata_m = "^\w+$"
        ret = re.match(pdata_m, output)
        if ret:
            return output
        pdata_m = "(\w+ )+"
        ret = re.match(pdata_m, output)
        if ret:
            return [item for item in output.split()]

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con('cat ' + drv_file)
        if not output:
            msg = 'unknown power driver'
            self.verify(False, msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    def get_linux_cpu_attrs(self, core_num, name="cpuinfo_cur_freq"):
        freq_path = "/sys/devices/system/cpu/cpu{0}/cpufreq/{1}".format(
            core_num, name)
        output = self.d_a_con("cat %s" % freq_path)
        return self.convert_to_values(output)

    def set_single_core_turbo(self, vcpu, status):
        '''
        status: enable_turbo | disable_turbo
        '''
        dut_core_index = self.vcpu_map[vcpu]
        self.guest_set_vm_turbo_status(vcpu, status)
        return int(dut_core_index)

    def get_expected_turbo_freq(self, core_index, status='disable'):
        info = self.cpu_info.get(core_index, {})
        value = info.get('scaling_available_frequencies')
        expected_freq = value[-2] if status == 'disable' else value[-1]
        return expected_freq

    def check_dut_core_turbo_enable(self, vcpu):
        dut_core_index = self.set_single_core_turbo(vcpu, 'enable_turbo')
        cur_freq = self.get_linux_cpu_attrs(dut_core_index)
        expected_freq = self.get_expected_turbo_freq(dut_core_index, 'enable')
        if cur_freq != expected_freq:
            msg = ("core <{0}> turbo status: cur frequency is <{1}> "
                   "not as expected frequency <{2}>").format(
                        dut_core_index, cur_freq, expected_freq)
            raise VerifyFailure(msg)
        self.logger.info(
            "core <{0}> turbo status set successful".format(dut_core_index))

    def check_dut_core_turbo_disable(self, vcpu):
        dut_core_index = self.set_single_core_turbo(vcpu, 'disable_turbo')
        cur_freq = self.get_linux_cpu_attrs(dut_core_index)
        expected_freq = self.get_expected_turbo_freq(dut_core_index, 'disable')
        if cur_freq != expected_freq:
            msg = ("core <{0}> turbo status: cur frequency is <{1}> "
                   "not as expected frequency <{2}>").format(
                        dut_core_index, cur_freq, expected_freq)
            raise VerifyFailure(msg)
        self.logger.info(
            "core <{0}> turbo status disable successful".format(dut_core_index))

    def get_expected_freq(self, core_index, check_item):
        freqs = {
            'max': 'scaling_max_freq',
            'medium': 'scaling_available_frequencies',
            'min': 'scaling_min_freq'}
        info = self.cpu_info.get(core_index, {})
        value = info.get(freqs.get(check_item))
        expected_freq = value if check_item != 'medium' else \
            sorted(value)[len(value) / 2]
        return expected_freq

    def check_core_freq(self, content):
        '''
        check core running frequency is the expected status
        high workload: maximum cpu frequency
        media workload: medium cpu frequency
        low workload: minimum cpu frequency
        '''
        check_item = content.get('check')
        real_freq = self.cur_cpu_freq
        self.logger.warning(real_freq)
        expected_freq = self.get_expected_freq(self.check_core, check_item)
        msg = (
            'core <{0}> freq <{1}> are not '
            'the expected frequency <{2}>').format(
                self.check_core, real_freq, expected_freq)
        self.verify(real_freq == expected_freq, msg)
        msg = 'core <{0}> are running on the expected frequency <{1}>'.format(
            self.check_core, expected_freq)
        self.logger.info(msg)

    def run_test_pre(self, policy_name):
        # boot up binary processes
        self.start_vm_power_mgr()
        # set binary process command
        self.set_vm_power_mgr()
        if policy_name == self.TRAFFIC:
            # boot up binary processes
            self.start_vm_testpmd()
            # set binary process command
            self.set_vm_testpmd()

    def run_test_post(self):
        # close all binary processes
        self.close_vm_testpmd()
        self.close_guest_mgr()
        self.close_vm_power_mgr()

    def run_guest_pre(self, content):
        self.preset_core_freq()
        # boot up binary processes
        self.start_guest_mgr(content.get('option', ''))
        # set binary process command
        self.guest_send_policy()

    def run_guest_post(self):
        # close guest
        self.close_guest_mgr()

    def traffic_policy(self, name, content):
        expected_pps = content['pps']
        test_pps = random.randint(expected_pps[0], expected_pps[1] - 1) \
            if isinstance(expected_pps, list) \
            else expected_pps
        msg = "run traffic with pps {0}".format(test_pps)
        self.logger.info(msg)
        info = {
            'stm_types': ['UDP_1'],
            'pps': expected_pps}
        # run traffic
        self.run_traffic(info)

    def run_policy(self, name, content):
        """ Measure cpu frequency fluctuate with work load """
        except_content = None
        try:
            self.run_guest_pre(content)
            # run traffic
            if name == self.TRAFFIC:
                self.traffic_policy(name, content)
            else:
                # run time policy, wait 10 second to make sure system ready
                # and get enough query data
                time.sleep(15)
                self.query_cpu_freq()
            # check cpu core status
            self.check_core_freq(content)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            # clear testing environment
            self.run_guest_post()

        if except_content:
            raise VerifyFailure(except_content)

    def get_policy_test_content(self, policy_name, vm_name, edge=False):
        '''
        -n or --vm-name
           sets the name of the vm to be used by the host OS.
        -b or --busy-hours
           sets the list of hours that are predicted to be busy
        -q or --quiet-hours
           sets the list of hours that are predicted to be quiet
        -l or --vcpu-list
           sets the list of vcpus to monitor
        -o or --policy
           sets the default policy type
              ``TIME``
              ``TRAFFIC``

        The format of the hours or list parameters is a comma-separated
        list of integers, which can take the form of
           a. x    e.g. --vcpu-list=1
           b. x,y  e.g. --quiet-hours=3,4
           c. x-y  e.g. --busy-hours=9-12
           d. combination of above (e.g. --busy-hours=4,5-7,9)
        '''
        policy_opt = '--policy={policy}'  # four types
        vm_opt = '--vm-name={vm}'
        vcpu_opt = '--vcpu-list={vcpus}'  # full cores/one core/multiple cores
        time_b_opt = '--busy-hours={hours}'  # all day/one hour/mixed range
        time_q_opt = '--quiet-hours={hours}'  # all day/one hour/mixed range
        # common option used by all policy
        opt_fmt = [vm_opt, policy_opt, vcpu_opt]
        # core option
        max_cores = len(self.vcpu_map)
        max_cores_list = ",".join([str(num) for num in range(max_cores)])
        cores_range = [max_cores_list] if edge else ['0', max_cores_list]
        # guest mgr option format configuration
        guest_opt = {
            'opt_fmt': opt_fmt,
            'option': {
                'vm': [vm_name],
                'vcpus': cores_range,
            }
        }
        # testing content
        policy_configs = {
            # traffic policy option
            self.TRAFFIC: [
                # low
                {'sys_hours': ['08:00', '10:00'],
                 'pps': 97000,  # below 1800000,
                 'check': 'min'},
            ],
            # time policy option
            self.TIME: [
                # quiet hours
                {'cmd': {
                 'opt_fmt': [time_q_opt],
                 'option':{
                     # use 23:00 as default time to run test
                     'hours': ['23'] if edge else ['23', '0-23', '4,5-7,23']}},
                 'sys_hours': ['23:00'],
                 'check': 'min'},
                # busy hours
                {'cmd': {
                 'opt_fmt': [time_b_opt],
                 'option':{
                     'hours': ['23'] if edge else ['23', '0-23', '4,5-7,23']}},
                    'sys_hours': ['23:00'],
                    'check': 'max'},
            ],
        }

        select_config = policy_configs.get(policy_name)
        # make combine testing options
        test_content = []
        for config in select_config:
            _common_config = deepcopy(guest_opt)
            if 'cmd' in config:
                option_cfg = config.get('cmd')
                _common_config['opt_fmt'] += option_cfg.get('opt_fmt', [])
                _common_config['option'].update(option_cfg['option'])
                config.pop('cmd')
            values = list(_common_config['option'].values())
            keys = list(_common_config['option'].keys())
            opt_fmt = _common_config['opt_fmt']
            for item in product(*values):
                _options = dict(list(zip(keys, item)))
                _options['policy'] = policy_name
                _opt_fmt = " ".join(opt_fmt)
                _config = deepcopy(config)
                _config['option'] = _opt_fmt.format(**_options)
                _config['vcpus'] = _options['vcpus']
                test_content.append(_config)

        return test_content

    def verify_policy(self, policy_name):
        test_contents = self.get_policy_test_content(
            policy_name, self.vm_name, edge=not self.full_test)
        msg = "begin test policy <{}> ...".format(policy_name)
        self.logger.info(msg)
        except_content = None
        try:
            self.run_test_pre(policy_name)
            for content in test_contents:
                self.logger.debug(pformat(content))
                # set system time
                pre_time, ori_sys_time = \
                    self.set_desired_time(content.get('sys_hours'))
                # run policy testing
                self.run_policy(policy_name, content)
                # restore system time
                self.restore_system_time(pre_time, ori_sys_time)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()

        if except_content:
            raise VerifyFailure(except_content)

        msg = "test policy <{}> successful !".format(policy_name)
        self.logger.info(msg)

    def verify_turbo_command(self, status):
        msg = "begin test turbo <{}> ...".format(status)
        self.logger.info(msg)
        except_content = None
        test_content = self.get_policy_test_content(
            self.TIME, self.vm_name, edge=True)[0]
        try:
            self.run_test_pre('turbo')
            self.start_guest_mgr(test_content.get('option'))
            check_func = getattr(
                self, 'check_dut_core_turbo_{}'.format(status))
            check_func(0)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()

        if except_content:
            raise VerifyFailure(except_content)

        msg = "test turbo <{}> successful !".format(status)
        self.logger.info(msg)

    def verify_power_driver(self):
        expected_drv = 'acpi-cpufreq'
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv)
        self.verify(power_drv == expected_drv, msg)

    def verify_cpupower_tool(self):
        name = 'cpupower'
        cmd = "whereis {} > /dev/null 2>&1; echo $?".format(name)
        output = self.d_a_con(cmd)
        status = True if output and output.strip() == "0" else False
        msg = '<{}> tool have not installed on DUT'.format(name)
        self.verify(status, msg)

    def preset_test_environment(self):
        self.is_mgr_on = self.is_pmd_on = None
        self.ext_con = {}
        # get cpu cores information
        self.dut.init_core_list_uncached_linux()
        self.cpu_info = self.get_all_cpu_attrs()
        # port management
        self.cur_drv = self.bind_ports_to_sys()
        self.used_port = 0
        # modprobe msr module to let the application can get the CPU HW info
        self.d_a_con('modprobe msr')
        self.d_a_con('cpupower frequency-set -g userspace > /dev/null 2>&1')
        # boot up vm
        self.start_vm()
        # init binary/tools
        self.init_vm_power_mgr()
        self.init_vm_testpmd()
        self.init_guest_mgr()
        # set branch ratio test value
        self.check_core = int(self.vcpu_map[0])
        self.cur_cpu_freq = None
        # used to control testing range. When run with full test, cover all
        # possible command line options combination, it will be long time.
        self.full_test = False
    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Not enough ports")
        self.verify_cpupower_tool()
        self.verify_power_driver()
        # prepare testing environment
        self.preset_test_environment()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_vm()
        self.bind_ports_to_dpdk(self.cur_drv)

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

    def test_perf_turbo_enable(self):
        """
        verify turbo enable command
        """
        self.verify_turbo_command('enable')

    def test_perf_turbo_disable(self):
        """
        verify turbo disable command
        """
        self.verify_turbo_command('disable')

    def test_perf_policy_traffic(self):
        """
        Measure cpu frequency fluctuate with traffic policy
        """
        self.verify_policy(self.TRAFFIC)

    def test_perf_policy_time(self):
        """
        Measure cpu frequency fluctuate with time policy
        """
        self.verify_policy(self.TIME)
