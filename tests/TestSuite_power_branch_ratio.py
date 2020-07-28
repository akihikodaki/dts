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
virtual power manager policy branch ratio test suite.
"""
import os
import re
import time
from contextlib import contextmanager
from copy import deepcopy
from pprint import pformat
import traceback


from utils import create_mask as dts_create_mask
from qemu_libvirt import LibvirtKvm
from pktgen import TRANSMIT_CONT
from exception import VerifyFailure
from settings import HEADER_SIZE
from packet import Packet
from test_case import TestCase


class TestPowerBranchRatio(TestCase):
    BRANCH_RATIO = "BRANCH_RATIO"
    vm_name = 'vm0'
    vm_max_ch = 8

    @property
    def target_dir(self):
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def get_cores_mask(self, config='all', crb=None):
        _crb = crb if crb else self.dut
        ports_socket = 0 if crb else _crb.get_numa_id(_crb.get_ports()[0])
        mask = dts_create_mask(_crb.get_core_list(config, socket=ports_socket))
        return mask

    def prepare_binary(self, name, host_crb=None):
        _host_crb = host_crb if host_crb else self.dut
        example_dir = "examples/" + name
        out = _host_crb.build_dpdk_apps('./' + example_dir)
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        binary_dir = os.path.join(self.target_dir, example_dir, 'build')
        cmd = ["ls -F {0} | grep --color=never '*'".format(binary_dir), '# ', 5]
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
        if len(cmds) == 0:
            return
        if isinstance(cmds, str):
            cmds = [cmds, '# ', 5]
        if not isinstance(cmds[0], list):
            cmds = [cmds]
        outputs = [] if len(cmds) > 1 else ''
        console, msg_pipe = self.get_console(name)
        if not console or not msg_pipe:
            return
        for item in cmds:
            try:
                expected_str = item[1] or '# '
                timeout = int(item[2]) if len(item) == 3 else 5
                output = console(item[0], expected_str, timeout)
            except Exception as e:
                msg = "execute '{0}' timeout".format(item[0])
                raise Exception(msg)
            time.sleep(0.5)
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

    def get_pkt_len(self, pkt_type, frame_size=1024):
        headers_size = sum([HEADER_SIZE[x] for x in ['eth', 'ip', pkt_type]])
        pktlen = frame_size - headers_size
        return pktlen

    def config_stream(self, dut_port_id, stm_name):
        dmac = self.dut.get_mac_address(dut_port_id)
        # set streams for traffic
        pkt_name = 'udp'
        pkt_configs = {
            'UDP_1': {
                'type': pkt_name.upper(),
                'pkt_layers': {
                    'ether': {'dst': dmac},
                    'raw': {'payload': ['58'] * self.get_pkt_len(pkt_name, frame_size=self.frame_size)}}},
        }
        # create packet for send
        if stm_name not in list(pkt_configs.keys()):
            msg = '{} not set'.format(stm_name)
            raise VerifyFailure(msg)
        values = pkt_configs[stm_name]
        pkt_type = values.get('type')
        pkt_layers = values.get('pkt_layers')
        pkt = Packet(pkt_type=pkt_type)
        for layer in list(pkt_layers.keys()):
            pkt.config_layer(layer, pkt_layers[layer])
        return pkt.pktgen.pkt

    def add_stream_to_pktgen(self, txport, rxport, send_pkts, option):
        stream_ids = []
        _option = deepcopy(option)
        _option['pcap'] = send_pkts[0]
        stream_id = self.tester.pktgen.add_stream(txport, rxport, send_pkts[0])
        self.tester.pktgen.config_stream(stream_id, _option)
        stream_ids.append(stream_id)
        _option = deepcopy(option)
        _option['pcap'] = send_pkts[1]
        stream_id = self.tester.pktgen.add_stream(rxport, txport, send_pkts[1])
        self.tester.pktgen.config_stream(stream_id, _option)
        stream_ids.append(stream_id)
        return stream_ids

    def traffic(self, option):
        txport = option.get('tx_intf')
        rxport = option.get('rx_intf')
        rate_percent = option.get('rate_percent', float(100))
        duration = option.get('duration', 15)
        send_pkts = option.get('stream') or []
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        s_option = {
            'stream_config': {
                'txmode': {},
                'transmit_mode': TRANSMIT_CONT,
                'rate': rate_percent, }
        }
        stream_ids = self.add_stream_to_pktgen(
            txport, rxport, send_pkts, s_option)
        # traffic options
        traffic_opt = {
            'method': 'throughput',
            'callback': self.query_cpu_freq,
            'interval': duration - 2,
            'duration': duration, }
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)

        return result

    def run_traffic(self, option):
        tester_tx_port_id = self.tester.get_local_port(self.dut_ports[0])
        tester_rx_port_id = self.tester.get_local_port(self.dut_ports[1])
        stm_type = option.get('stm_type')
        duration = option.get('duration', None) or 15
        ports_topo = {
            'tx_intf': tester_tx_port_id,
            'rx_intf': tester_rx_port_id,
            'stream': [
                self.config_stream(self.dut_ports[0], stm_type),
                self.config_stream(self.dut_ports[1], stm_type), ],
            'duration': duration, }
        result = self.traffic(ports_topo)

        return result

    def create_powermonitor_folder(self):
        # create temporary folder for power monitor
        cmd = 'mkdir -p {0}; chmod 777 {0}'.format(self.vm_log_dir)
        self.d_a_con(cmd)

    def init_vms_params(self):
        self.vcpu_map = self.vcpu_lst = self.vm = self.vm_dut = self.guest_session = None
        self.vm_log_dir = '/tmp/powermonitor'
        self.create_powermonitor_folder()

    def add_pf_device(self, pci_addr, vm_inst):
        vm_params = {
            'driver': 'pci-assign',
            'driver': 'vfio',
            'opt_host': pci_addr,
            'guestpci':  '0000:00:07.0'}
        vm_inst.set_vm_device(**vm_params)

    def start_vm(self):
        '''
        '''
        # set vm initialize parameters
        self.init_vms_params()
        # start vm
        self.vm = LibvirtKvm(self.dut, self.vm_name, self.suite_name)
        # pass pf to virtual machine
        pci_addr = self.dut.get_port_pci(self.dut_ports[0])
        self.add_pf_device(pci_addr, self.vm)
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
        self.vcpu_map = [int(core) for core in self.vm.get_vm_cpu()]
        self.vcpu_lst = [int(item['core']) for item  in self.vm_dut.cores]

    def close_vm(self):
        '''
        '''
        if not self.is_vm_on:
            return
        if self.guest_session:
            self.vm_dut.close_session(self.guest_session)
        self.vm.stop()
        self.vm = None
        self.is_vm_on = False
        self.dut.virt_exit()
        cmd_fmt = 'virsh {0} {1} > /dev/null 2>&1'.format
        cmds = [
            [cmd_fmt('shutdown', self.vm_name), '# '],
            [cmd_fmt('undefine', self.vm_name), '# '], ]
        self.d_a_con(cmds)

    def preset_compilation(self):
        '''
        '''
        sw_table = [
            "CONFIG_RTE_LIBRTE_POWER",
            "CONFIG_RTE_LIBRTE_POWER_DEBUG",
        ]
        for sw in sw_table:
            cmd = ("sed -i -e "
                   "'s/{0}=n$/{0}=y/' "
                   "{1}/config/common_base").format(sw, self.target_dir)
            self.d_a_con(cmd)
        # re-compile dpdk source code
        self.dut.build_install_dpdk(self.target)

    @contextmanager
    def restore_environment(self):
        try:
            yield
        finally:
            time.sleep(10)
            self.restore_port_drv()
            sw_table = [
                "CONFIG_RTE_LIBRTE_POWER",
                "CONFIG_RTE_LIBRTE_POWER_DEBUG",
            ]
            for sw in sw_table:
                cmd = ("sed -i -e "
                       "'s/{0}=y$/{0}=n/' "
                       "{1}/config/common_base").format(sw, self.target_dir)
                self.d_a_con(cmd)
            # re-compile dpdk source code
            self.dut.build_install_dpdk(self.target)

    def restore_port_drv(self):
        driver = self.drivername
        for port in self.dut.ports_info:
            netdev = port.get('port')
            if not netdev:
                continue
            cur_drv = netdev.get_nic_driver()
            if cur_drv == driver:
                continue
            netdev.bind_driver(driver)

    def init_vm_power_mgr(self):
        self.vm_power_mgr = self.prepare_binary('vm_power_manager')

    def start_vm_power_mgr(self):
        sub_option = (
            '-v '
            '-c {core_mask} '
            '-n {mem_channel} '
            '-m {memory_size} '
            '--no-pci ').format(**{
                'core_mask': self.get_cores_mask("1S/3C/1T"),
                'mem_channel': self.dut.get_memory_channels(),
                'memory_size': 1024, })
        prompt = 'vmpower>'
        option = sub_option + \
            (' -- --core-branch-ratio={}'.format(self.branch_ratio) \
            if self.branch_ratio else '')
        cmd = [' '.join([self.vm_power_mgr, option]), prompt, 50]
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
        self.d_con(['quit', '# ', 30])
        self.is_mgr_on = False

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
            '-v '
            '-c {core_mask} '
            '-n {memory_channel} '
            '-m {memory_size} '
            '--no-pci '
            '--file-prefix={file_prefix} '
            '-- '
            '--vm-name={vm_name} '
            '--policy={policy} '
            '--vcpu-list={vpus} ').format(**{
                'core_mask': '0xff',
                'memory_channel': self.vm_dut.get_memory_channels(),
                'memory_size': 1024,
                'policy': self.BRANCH_RATIO,
                'file_prefix': 'vmpower1',
                'vm_name': self.vm_name,
                'vpus': ','.join(
                    [str(index) for index in self.vcpu_lst]),
            })
        guest_cmd = ' '.join([self.guest_cli, option])
        self.vm_g_con([guest_cmd, prompt, 120])
        self.is_guest_on = True

    def send_policy_on_guest_mgr(self):
        self.vm_g_con(['send_policy now', r"vmpower\(guest\)>", 20])

    def close_guest_mgr(self):
        if not self.is_guest_on:
            return
        self.vm_g_con("quit")
        self.is_guest_on = False

    def init_vm_testpmd(self):
        self.vm_testpmd = "{}/{}/app/testpmd".format(
            self.target_dir, self.dut.target)

    def start_vm_testpmd(self):
        cores = [0, 1]
        core_mask = dts_create_mask(cores)
        option = (
            '-v '
            '-c {core_mask} '
            '-n {mem_channel} '
            '-m {memsize} '
            '--file-prefix={file-prefix} '
            '-- -i ').format(**{
                'core_mask': core_mask,
                'mem_channel': self.vm_dut.get_memory_channels(),
                'memsize': 1024,
                'file-prefix': 'vmpower2', })

        cmd = ' '.join([self.vm_testpmd, option])
        self.vm_con([cmd, "testpmd> ", 120])
        self.is_pmd_on = True

    def set_vm_testpmd(self):
        cmd = 'start'
        self.vm_con([cmd, "testpmd> ", 15])

    def close_vm_testpmd(self):
        if not self.is_pmd_on:
            return
        self.vm_con(['quit', '# ', 15])
        self.is_pmd_on = False

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con('cat ' + drv_file)
        if not output:
            msg = 'unknown power driver'
            raise VerifyFailure(msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    def query_cpu_freq(self):
        cmd = ';'.join([
            "cat /sys/devices/system/cpu/cpu{0}/cpufreq/scaling_min_freq",
            "cat /sys/devices/system/cpu/cpu{0}/cpufreq/scaling_max_freq"
            ]).format(self.check_core)
        output = self.d_a_con(cmd)
        if not output:
            self.scaling_min_freq, self.scaling_max_freq = 0, 0
        else:
            values = [int(item) for item in output.splitlines()]
            self.scaling_min_freq, self.scaling_max_freq = values

    def get_core_scaling_max_freq(self, core_index):
        cpu_attr = '/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_max_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_con(cmd)
        return int(output)

    def get_core_scaling_min_freq(self, core_index):
        cpu_attr = '/sys/devices/system/cpu/cpu{0}/cpufreq/scaling_min_freq'
        cmd = 'cat ' + cpu_attr.format(core_index)
        output = self.d_a_con(cmd)
        return int(output)

    def get_no_turbo_max(self):
        cmd = 'rdmsr -p {} 0x0CE -f 15:8 -d'.format(self.check_core)
        output = self.d_a_con(cmd)
        freq = output.strip() + '00000'
        return int(freq)

    def get_all_cpu_attrs(self):
        ''' get all cpus' attribute '''
        cpu_attrs = ['cpuinfo_max_freq', 'cpuinfo_min_freq']
        freq = '/sys/devices/system/cpu/cpu{0}/cpufreq/{1}'.format
        cpu_topos = self.dut.get_all_cores()
        cpu_info = {}
        for cpu_topo in cpu_topos:
            cpu_id = int(cpu_topo['thread'])
            cpu_info[cpu_id] = {}
            cpu_info[cpu_id]['socket'] = cpu_topo['socket']
            cpu_info[cpu_id]['core'] = cpu_topo['core']

        for cpu_attr in cpu_attrs:
            cmds = []
            for cpu_id in sorted(cpu_info.keys()):
                cmds.append('cat {0}'.format(freq(cpu_id, cpu_attr)))
            output = self.d_a_con(';'.join(cmds))
            freqs = [int(item) for item in output.splitlines()]
            for index, cpu_id in enumerate(sorted(cpu_info.keys())):
                cpu_info[cpu_id][cpu_attr] = freqs[index]

        return cpu_info

    def run_test_pre(self):
        # boot up binary processes
        self.start_vm_power_mgr()
        # set binary process command
        self.set_vm_power_mgr()
        # boot up binary processes
        self.start_guest_mgr()
        # set binary process command
        self.send_policy_on_guest_mgr()
        # boot up binary processes
        self.start_vm_testpmd()
        # set binary process command
        self.set_vm_testpmd()

    def run_test_post(self):
        # close all binary processes
        self.close_vm_testpmd()
        self.close_guest_mgr()
        self.close_vm_power_mgr()

    def check_core_freq_in_traffic(self, core_index):
        '''
        check the cores frequency when running traffic
             highest frequency[no_turbo_max]: cur_min=cur_max=no_turbo_max
        '''
        expected_freq = self.get_no_turbo_max()
        msg = 'max freq is failed to get.'
        self.verify(self.scaling_max_freq, msg)
        msg = 'max freq is not the same as highest frequency <{0}>'
        self.verify(expected_freq == self.scaling_max_freq,
                    msg.format(expected_freq))
        msg = 'min freq is failed to get.'
        self.verify(self.scaling_min_freq, msg)
        msg = 'min freq is not the same as highest frequency <{0}>'
        self.verify(expected_freq == self.scaling_min_freq,
                    msg.format(expected_freq))
        msg = "core <{0}> action is ok in traffic".format(core_index)
        self.logger.info(msg)

    def check_vm_power_mgr_output(self):
        '''
        check the branch miss ration and the related CPU frequency, the core
        used by testpmd as worker core will be shown as branch ratio value.
        '''
        output = self.dut.get_session_output(timeout=2)
        msg = 'virtual machine testpmd has not output message'
        self.verify(output, msg)
        pat = '.*\s+(\d+): ([0-9\.]+) \{(\d+)\} \{(\d+)\}.*'
        core_branch_ratio = re.findall(pat, output)
        msg = 'virtual machine testpmd has not branch ratio output message'
        self.verify(core_branch_ratio, msg)
        self.logger.info(pformat(core_branch_ratio))
        msg = "branch ratio output is ok"
        self.logger.info(msg)

    def check_dut_core_freq(self, core_index, ref_freq_name):
        '''
        Check the core frequency, the frequency reported should be::
            [sys_min]: cur_min=cur_max=sys_min
        '''
        expected_freq = self.cpu_info.get(core_index, {}).get(ref_freq_name)
        max_freq = self.get_core_scaling_max_freq(core_index)
        min_freq = self.get_core_scaling_min_freq(core_index)
        msg = 'max freq<{0}>/min_freq<{1}>/expected freq<{2}> are not the same'
        self.verify(
            max_freq == min_freq and max_freq == expected_freq,
            msg.format(max_freq, min_freq, expected_freq))
        msg = "core <{0}> action is ok after traffic stop".format(core_index)
        self.logger.info(msg)

    def verify_branch_ratio(self):
        except_content = None
        msg = "begin test policy <{0}> ...".format(self.BRANCH_RATIO)
        self.logger.info(msg)
        try:
            # prepare testing binary
            self.run_test_pre()
            # run traffic
            option = {'stm_type': 'UDP_1', }
            self.run_traffic(option)
            time.sleep(10)
            # check test result
            self.check_core_freq_in_traffic(self.check_core)
            self.check_vm_power_mgr_output()
            self.check_dut_core_freq(self.check_core, 'cpuinfo_min_freq')
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.run_test_post()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        msg = "test policy <{0}> successful !!!".format(self.BRANCH_RATIO)
        self.logger.info(msg)

    def verify_power_driver(self):
        expected_drv = 'intel_pstate'
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv)
        self.verify(power_drv == expected_drv, msg)

    def check_cpupower_tool(self):
        cmd = "whereis cpupower > /dev/null 2>&1; echo $?"
        output = self.d_a_con(cmd)
        status = True if output and output.strip() == "0" else False
        msg = 'cpupower tool have not installed on DUT'
        self.verify(status, msg)

    def init_params(self):
        self.is_mgr_on = self.is_guest_on = self.is_pmd_on = \
            self.is_vm_on = None
        self.ext_con = {}
        # set branch ratio test value
        self.branch_ratio = None

    def preset_test_environment(self):
        self.dut.init_core_list_uncached_linux()
        self.cpu_info = self.get_all_cpu_attrs()
        # modprobe msr module to let the application can get the CPU HW info
        self.d_a_con('modprobe msr')
        self.d_a_con('cpupower frequency-set -g userspace > /dev/null 2>&1')
        # compile
        self.preset_compilation()
        # boot up vm
        self.start_vm()
        # init binary
        self.init_vm_power_mgr()
        self.init_vm_testpmd()
        self.init_guest_mgr()
        test_content = self.get_suite_cfg()
        self.frame_size = test_content.get('frame_size') or 1024
        self.check_ratio = test_content.get('check_ratio') or 0.1
        self.check_core = self.vcpu_map[1]
        msg = "select dut core {} as check core".format(self.check_core)
        self.logger.info(msg)
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.init_params()
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
        with self.restore_environment():
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

    def test_perf_basic_branch_ratio(self):
        """
        Basic branch-ratio test based on one NIC pass-through into VM scenario
        """
        self.branch_ratio = None
        self.verify_branch_ratio()

    def test_perf_set_branch_ratio_rate_by_user(self):
        """
        Set Branch-Ratio Rate by User
        """
        self.branch_ratio = self.check_ratio
        self.verify_branch_ratio()
