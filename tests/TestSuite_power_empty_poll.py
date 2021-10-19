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
power empty poll test suite.
"""
import os
import time
import traceback
from copy import deepcopy
from pprint import pformat

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.settings import HEADER_SIZE, PKTGEN_TREX
from framework.test_case import TestCase
from framework.utils import create_mask as dts_create_mask


class TestPowerEmptyPoll(TestCase):
    TRAIN = 'train'
    NOTRAIN = 'no-train'
    MED = 'med_threshold'
    HIGH = 'high_threshold'

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    @property
    def is_use_trex(self):
        return (hasattr(self.tester, 'is_pktgen') and
                self.tester.is_pktgen and
                self.tester.pktgen.pktgen_type == PKTGEN_TREX)

    def d_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.dut.alt_session.send_expect(*_cmd)

    def prepare_binary(self, name):
        example_dir = "examples/" + name
        out = self.dut.build_dpdk_apps('./' + example_dir)
        return os.path.join(self.target_dir,
                            self.dut.apps_name[os.path.basename(name)])

    def get_cores_mask(self, cores_list):
        return dts_create_mask(cores_list)

    def add_stream_to_pktgen(self, txport, rxport, send_pkts, option):
        stream_ids = []
        cnt = 0
        for pkt in send_pkts:
            _option = deepcopy(option)
            _option['pcap'] = pkt
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
            # rxport -> txport
            stream_id = self.tester.pktgen.add_stream(rxport, txport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
            cnt += 1
        return stream_ids

    def run_traffic(self, option):
        txport = self.tester.get_local_port(self.dut_ports[0])
        rxport = self.tester.get_local_port(self.dut_ports[1])
        stm_type = option.get('stm_types')
        rate_percent = option.get('rate', float(100))
        duration = option.get('duration', 10)
        send_pkts = self.set_stream(stm_type)
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        s_option = {
            'stream_config': {
                'txmode': {},
                'transmit_mode': TRANSMIT_CONT,
                'rate': rate_percent, }
        }
        stream_ids = self.add_stream_to_pktgen(txport, rxport, send_pkts, s_option)
        # run traffic options
        traffic_opt = option.get('traffic_opt')
        # run pktgen(ixia/trex) traffic
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)

        return result

    def get_pkt_len(self, pkt_type, frame_size):
        headers_size = sum([HEADER_SIZE[x] for x in ['eth', 'ip', pkt_type]])
        pktlen = frame_size - headers_size
        return pktlen

    def set_stream(self, stm_names=None):
        # set streams for traffic
        pkt_configs = {
            'UDP_1': {
                'type': 'UDP',
                'pkt_layers': {
                    'ipv4': {'dst': '1.1.1.1'},
                    'raw': {'payload': ['58'] * self.get_pkt_len('udp', frame_size=self.frame_size)}}},
        }
        # create packet instance for send
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

        return streams

    @property
    def empty_poll_options(self):
        table = {
            'train': '1,0,0',
            'no-train': '0,350000,500000', }
        return table

    def init_l3fwd_power(self):
        self.l3fwd_power = self.prepare_binary('l3fwd-power')

    def start_l3fwd_power(self, core):
        train_mode = self.empty_poll_options.get(self.train_mode)
        option = ('-v '
                  '-c {core_mask} '
                  '-n {mem_channel} '
                  '-- '
                  '-p 0x3 '
                  '-P '
                  '--config="(0,0,{core}),(1,0,{core})" '
                  '-l 10 -m 6 -h 1 '
                  '--empty-poll="{empty-poll}" '
                  ).format(**{
                      'core': core[-1],
                      'core_mask': self.get_cores_mask(core),
                      'mem_channel': self.dut.get_memory_channels(),
                      'empty-poll': train_mode, })
        prompts = {
            self.NOTRAIN: 'POWER: Bring up the Timer',
            self.TRAIN: 'POWER: Training is Complete'}
        prompt = prompts.get(self.train_mode)
        cmd = [' '.join([self.l3fwd_power, option]), prompt, 120]
        self.d_con(cmd)
        self.is_l3fwd_on = True

    def close_l3fwd_power(self):
        if not self.is_l3fwd_on:
            return
        cmd = "^C"
        self.d_con(cmd)

    def is_hyper_threading(self):
        cpu_index = list(self.cpu_info.keys())[-1]
        core_num = self.cpu_info[cpu_index].get('core')
        return (cpu_index + 1) / 2 == (core_num + 1)

    def is_support_pbf(self):
        # check if cpu support bpf feature
        cpu_attr = r'/sys/devices/system/cpu/cpu0/cpufreq/base_frequency'
        cmd = "ls {0}".format(cpu_attr)
        self.d_a_con(cmd)
        cmd = "echo $?"
        output = self.d_a_con(cmd)
        ret = True if output == "0" else False
        return ret

    def query_cpu_freq(self):
        cmd = (
            "cat /sys/devices/system/cpu/cpu{0}/cpufreq/scaling_min_freq;"
            "cat /sys/devices/system/cpu/cpu{0}/cpufreq/scaling_max_freq;"
        ).format(self.check_core[1])
        output = self.d_a_con(cmd)
        if not output:
            self.scaling_min_freq, self.scaling_max_freq = 0, 0
        else:
            values = [int(item) for item in output.splitlines()]
            self.scaling_min_freq, self.scaling_max_freq = values

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
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
        freq = '/sys/devices/system/cpu/cpu{0}/cpufreq/{1}'.format
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
            freqs = [int(item) for item in output.splitlines()] \
                if key_value != 'scaling_available_frequencies' else \
                    [item for item in output.splitlines()]
            for index, cpu_id in enumerate(sorted(cpu_info.keys())):
                if key_value == 'scaling_available_frequencies':
                    cpu_info[cpu_id][key_value] = \
                        [int(item) for item in sorted(freqs[index].split())]
                else:
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
            raise VerifyFailure(msg)
        self.logger.debug(pformat(base_freqs_info))

        return cpu_info, base_freqs_info

    def get_normal_cores_index(self, number):
        normal_freq = min(self.base_freqs_info.keys())
        cores_index = self.base_freqs_info[normal_freq][1:number] \
            if self.base_freqs_info[normal_freq][0] == 0 else \
            self.base_freqs_info[normal_freq][:number]
        return cores_index

    def get_no_turbo_max(self, core):
        cmd = 'rdmsr -p {} 0x0CE -f 15:8 -d'.format(core)
        output = self.d_a_con(cmd)
        freq = output.strip() + '00000'
        return int(freq)

    def check_core_freq_in_traffic(self, core_index, mode):
        '''
        check the cores frequency when running traffic
             highest frequency[no_turbo_max]: cur_min=cur_max=no_turbo_max
        '''
        freq = self.get_no_turbo_max(core_index)
        expected_freq = freq if mode == self.HIGH else (freq - 500000)
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
        msg = 'core <{0}>: max freq/min_freq/expected freq<{1}> are the same'
        self.logger.info(msg.format(core_index, expected_freq))

    def check_no_train(self):
        output = self.dut.get_session_output(timeout=2)
        msg = 'training steps should not be executed'
        self.verify('POWER: Training is Complete' not in output, msg)

    @property
    def train_mode_check_item(self):
        # Injected Rate:
        #      10G -> 0.1G -> 10G -> 0.1G -> 10G -> 0.1G
        check_item = [
            [100, self.HIGH],
            [1, self.MED],
            [100, self.HIGH],
            [1, self.MED],
            [100, self.HIGH],
            [1, self.MED], ]
        return check_item

    def verify_train_mode(self):
        except_content = None
        # begin run vm power policy testing
        try:
            self.start_l3fwd_power(self.check_core)
            if self.train_mode == self.NOTRAIN:
                self.check_no_train()
            else:
                time.sleep(10) # wait some time for stable training
                msg = '{0} begin test mode <{1}> with traffic rate percent {2}%'
                for rate, mode in self.train_mode_check_item:
                    self.logger.info(msg.format(self.train_mode, mode, rate))
                    duration = 20 if self.is_use_trex else 10
                    info = {
                        'traffic_opt': {
                            'method': 'throughput',
                            'interval': duration - 2,
                            'duration': duration,
                            'callback': self.query_cpu_freq},
                        'stm_types': ['UDP_1'],
                        'rate': rate}
                    # run traffic
                    self.run_traffic(info)
                    time.sleep(15 if self.is_use_trex else 2)
                    # check test result
                    self.check_core_freq_in_traffic(self.check_core[1], mode)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise VerifyFailure(except_content)
        else:
            msg = "test <{0}> successful !!!".format(self.train_mode)
            self.logger.info(msg)

    def verify_power_driver(self):
        expected_drv = 'intel_pstate'
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv)
        self.verify(power_drv == expected_drv, msg)

    def verify_hyper_threading(self):
        msg = "{} should work under hyper threading close status"
        self.verify(not self.is_hyper_threading(), msg.format(self.suite_name))

    def verify_pbf_supported(self):
        if self.is_support_pbf():
            return
        msg = "dut cpu doesn't support priority base frequency feature"
        raise VerifyFailure(msg)

    def preset_test_environment(self):
        self.is_l3fwd_on = None
        self.cpu_info, self.base_freqs_info = self.get_all_cpu_attrs()
        test_content = self.get_suite_cfg()
        self.frame_size = test_content.get('frame_size') or 1024
        self.check_core = self.get_normal_cores_index(2)
        self.verify_hyper_threading()
        # modprobe msr module to let the application can get the CPU HW info
        self.d_a_con('modprobe msr')
        # init binary
        self.init_l3fwd_power()
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify_power_driver()
        # check if cpu support bpf feature
        self.verify_pbf_supported()
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        # prepare testing environment
        self.preset_test_environment()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass

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

    def test_perf_basic_train_mode(self):
        """
        Set Branch-Ratio Rate by User
        """
        self.train_mode = self.TRAIN
        self.verify_train_mode()

    def test_perf_no_training_mode(self):
        """
        Set Branch-Ratio Rate by User
        """
        self.train_mode = self.NOTRAIN
        self.verify_train_mode()
