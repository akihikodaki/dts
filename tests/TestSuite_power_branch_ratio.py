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
import traceback
from contextlib import contextmanager
from copy import deepcopy
from pprint import pformat

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.qemu_libvirt import LibvirtKvm
from framework.settings import HEADER_SIZE, HOST_BUILD_TYPE_SETTING, load_global_setting
from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestPowerBranchRatio(TestCase):
    BRANCH_RATIO = "BRANCH_RATIO"

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
        return os.path.join(self.target_dir,
                            _host_crb.apps_name[os.path.basename(name)])

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

    def d_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.dut.alt_session.send_expect(*_cmd)

    def d_sys_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.alt_sys_session.send_expect(*_cmd)

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

    @property
    def compile_switch(self):
        sw_table = [
            "CONFIG_RTE_LIBRTE_POWER",
            "CONFIG_RTE_LIBRTE_POWER_DEBUG",
        ]
        return sw_table

    def preset_compilation(self):
        if 'meson' == load_global_setting(HOST_BUILD_TYPE_SETTING):
            compile_SWs = self.compile_switch + ["CONFIG_RTE_LIBRTE_I40E_PMD"]
            self.dut.set_build_options(dict([(sw[7:], 'y') for sw in compile_SWs]))
        else:
            for sw in self.compile_switch:
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
            try:
                self.restore_port_drv()
            except Exception as e:
                self.logger.error(traceback.format_exc())
            # restore compilation
            if 'meson' == load_global_setting(HOST_BUILD_TYPE_SETTING):
                self.dut.set_build_options(
                    dict([(sw[7:], 'n') for sw in self.compile_switch]))
            else:
                for sw in self.compile_switch:
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
            (' -- --core-branch-ratio={0}-{1}:{2}'.format(self.from_core, self.to_core, self.branch_ratio)
            if self.branch_ratio else '')
        cmd = [' '.join([self.vm_power_mgr, option]), prompt, 50]
        self.d_con(cmd)
        self.is_mgr_on = True

    def close_vm_power_mgr(self):
        if not self.is_mgr_on:
            return
        self.d_con(['quit', '# ', 30])
        self.is_mgr_on = False

    def add_alternative_session_to_dut(self):
        self.alt_sys_session = self.dut.create_session("alt_sys_session")

    def init_testpmd(self):
        self.testpmd = os.path.join(self.target_dir,
                                       self.dut.apps_name['test-pmd'])

    def start_testpmd(self):
        cores = []
        for core in self.testpmd_cores:
            cores.append(core)
        core_mask = dts_create_mask(cores)
        option = (
            '-v '
            '-c {core_mask} '
            '-n {mem_channel} '
            '-m {memsize} '
            '--file-prefix={file-prefix} '
            '-- -i ').format(**{
                'core_mask': core_mask,
                'mem_channel': self.dut.get_memory_channels(),
                'memsize': 1024,
                'file-prefix': 'vmpower2', })

        cmd = ' '.join([self.testpmd, option])
        self.d_a_con([cmd, "testpmd> ", 120])
        self.is_pmd_on = True

    def set_testpmd(self):
        cmd = 'start'
        self.d_a_con([cmd, "testpmd> ", 15])

    def close_testpmd(self):
        if not self.is_pmd_on:
            return
        self.d_a_con(['quit', '# ', 15])
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
            "cat /sys/devices/system/cpu/cpu{0}/cpufreq/scaling_cur_freq"
            ]).format(self.check_core)
        output = self.d_sys_con(cmd)
        if not output:
            self.scaling_cur_freq = 0
        else:
            self.scaling_cur_freq = round(int(output))

    def get_no_turbo_max(self):
        cmd = 'rdmsr -p {} 0x0CE -f 15:8 -d'.format(self.check_core)
        output = self.d_sys_con(cmd)
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
        # boot up binary processes
        self.start_testpmd()
        # set binary process command
        self.set_testpmd()


    def run_test_post(self):
        # close all binary processes
        self.close_testpmd()
        self.close_vm_power_mgr()

    def check_core_freq_in_traffic(self, core_index):
        '''
        check the cores frequency when running traffic
             highest frequency[no_turbo_max]: expected_freq(P1) <= cur_freq
        '''
        expected_freq = self.get_no_turbo_max()
        msg = 'failed to get cur freq.'
        self.verify(self.scaling_cur_freq, msg)
        msg = 'cur freq <{0}> is lower than expected freq <{1}>'
        self.verify(expected_freq <= self.scaling_cur_freq,
                    msg.format(self.scaling_cur_freq ,expected_freq))
        msg = "core <{0}> action is ok in traffic".format(core_index)
        self.logger.info(msg)
        displayFreqData = "Freqs in Traffic : Check Core Freq {0} >= Expected Freq {1}".format(self.scaling_cur_freq, expected_freq)
        self.logger.info(displayFreqData)

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

    def check_core_freq_no_traffic(self, core_index, ref_freq_name):
            '''
            Check the core frequency, the frequency reported should be::
                cur_freq <= sys_min
            '''
            expected_freq = self.cpu_info.get(core_index, {}).get(ref_freq_name)
            self.query_cpu_freq()
            time.sleep(1)
            msg = 'cur freq<{0}> is higher than /expected freq<{1}> in no traffic'
            self.verify(
                self.scaling_cur_freq <= expected_freq,
                msg.format(self.scaling_cur_freq, expected_freq))
            msg = "core <{0}> action is ok after traffic stop".format(core_index)
            self.logger.info(msg)
            displayFreqData = "Freqs in NO Traffic: Check Core Freq {0} <= Expected Freq {1}".format(self.scaling_cur_freq, expected_freq)
            self.logger.info(displayFreqData)

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
            self.check_core_freq_no_traffic(self.check_core, 'cpuinfo_min_freq')
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
        self.is_mgr_on = self.is_pmd_on = None
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
        # init binary
        self.init_vm_power_mgr()
        self.init_testpmd()
        self.add_alternative_session_to_dut()
        test_content = self.get_suite_cfg()
        self.frame_size = test_content.get('frame_size') or 1024
        self.check_ratio = test_content.get('check_ratio') or 0.1
        self.from_core = test_content.get('from_core')
        self.to_core = test_content.get('to_core')
        self.check_core = test_content.get('check_core')
        self.testpmd_cores = test_content.get('testpmd_cores')
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
        self.restore_environment()

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

    def test_perf_set_branch_ratio_rate_by_user(self):
        """
        Set Branch-Ratio Rate by User
        """
        self.branch_ratio = self.check_ratio
        self.verify_branch_ratio()
