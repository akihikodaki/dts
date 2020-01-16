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

"""
DPDK Test suite.
l3fwd-power power management test suite.
"""
import os
import time
import textwrap
import traceback
from copy import deepcopy

from utils import create_mask as dts_create_mask
from test_case import TestCase

from packet import Packet
from pktgen import TRANSMIT_CONT


class TestPowerEmptPoll(TestCase):
    TRAIN = 'train'
    NOTRAIN = 'no-train'
    MED = 'med_threshold'
    HIGH = 'high_threshold'
    query_min_freq = '/tmp/cpu_min.log'
    query_max_freq = '/tmp/cpu_max.log'
    output_path = '/tmp'

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def d_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.dut.send_expect(*_cmd)

    def d_a_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, str) else cmd
        return self.dut.alt_session.send_expect(*_cmd)

    def prepare_binary(self, name):
        example_dir = "examples/" + name
        out = self.dut.build_dpdk_apps('./' + example_dir)
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        binary_dir = os.path.join(self.target_dir, example_dir, 'build')
        cmd = ["ls -F {0} | grep '*'".format(binary_dir), '# ', 5]
        exec_file = self.d_a_con(cmd)
        binary_file = os.path.join(binary_dir, exec_file[:-1])
        return binary_file

    def get_cores_mask(self, cores_list):
        return dts_create_mask(cores_list)

    def set_pktgen_stream(self, txport, rxport, send_pkts, option):
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
        # set stream into pktgen
        option = {
            'stream_config': {
                'txmode': {},
                'transmit_mode': TRANSMIT_CONT,
                'rate': rate_percent, }
        }
        stream_ids = self.set_pktgen_stream(txport, rxport, send_pkts, option)
        # run traffic options
        traffic_opt = {
            'method': 'throughput',
            'duration': duration, }
        # run pktgen(ixia/trex) traffic
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)

        return result

    def set_stream(self, stm_names=None):
        # set streams for traffic
        pkt_configs = {
            'UDP_1': {
                'type': 'UDP',
                'pkt_layers': {'ipv4': {'dst': '1.1.1.1'}, }},
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
            'train': '1,0,0,',
            'no-train': '0,350000,500000', }
        return table

    def init_l3fwd_power(self):
        self.l3fwd_power = self.prepare_binary('l3fwd-power')

    def start_l3fwd_power(self, core):
        train_mode = self.empty_poll_options.get(self.train_mode)
        option = (' '
                  '-c {core_mask} '
                  '-n {mem_channel} '
                  '-- '
                  '-p 0x1 '
                  '-P '
                  '--config="(0,0,2)" '
                  '-l 10 -m 6 -h 1'
                  '--empty-poll="{empty-poll}" '
                  ).format(**{
                      'core_mask': self.get_cores_mask(core),
                      'mem_channel': self.dut.get_memory_channels(),
                      'empty-poll': train_mode, })
        prompt = 'L3FWD_POWER: entering main loop on lcore'
        cmd = [' '.join([self.l3fwd_power, option]), prompt, 60]
        self.d_con(cmd)

    def close_l3fwd_power(self):
        cmd = 'killall l3fwd-power'
        self.d_a_con(cmd)

    def init_query_script(self):
        script_content = textwrap.dedent("""
            # $1: delay time before traffic start
            # $2: core number
            sleep 5
            while :
            do
                sleep 1
                cat /sys/devices/system/cpu/cpu$1/cpufreq/scaling_min_freq >> {0}
                cat /sys/devices/system/cpu/cpu$1/cpufreq/scaling_max_freq >> {1}
            done
        """).format(self.query_min_freq, self.query_max_freq)
        fileName = 'vm_power_core.sh'
        query_script = os.path.join(self.output_path, fileName)
        with open(query_script, 'wb') as fp:
            fp.write('#! /bin/sh' + os.linesep + script_content)
        self.dut.session.copy_file_to(query_script, self.target_dir)
        self.query_tool = ';'.join([
            'cd {}'.format(self.target_dir),
            'chmod 777 {}'.format(fileName),
            './' + fileName])

    def start_query(self, core):
        cmd = self.query_tool + ' {0} > /dev/null 2>&1 &'.format(core)
        self.d_a_con(cmd)

    def stop_query(self):
        cmd = 'pkill {}'.format(os.path.basename(self.query_tool))
        self.d_a_con(cmd)
        self.dut.session.copy_file_from(self.query_min_freq, self.output_path)
        self.dut.session.copy_file_from(self.query_max_freq, self.output_path)

    def get_sys_power_driver(self):
        drv_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver"
        output = self.d_a_con('cat ' + drv_file)
        if not output:
            msg = 'unknown power driver'
            self.verify(False, msg)
        drv_name = output.splitlines()[0].strip()
        return drv_name

    def get_no_turbo_max(self):
        cmd = 'rdmsr -p 1 0x0CE -f 15:8 -d'
        output = self.d_a_con(cmd)
        freq = output.strip() + '00000'
        return int(freq)

    def check_core_freq_in_traffic(self, core_index, mode):
        '''
        check the cores frequency when running traffic
             highest frequency[no_turbo_max]: cur_min=cur_max=no_turbo_max
        '''
        self.stop_query()
        freq = self.get_no_turbo_max()
        expected_freq = str(freq if mode == self.HIGH else (freq - 500000))
        query_max_freq = os.path.join(
            self.output_path, os.path.basename(self.query_max_freq))
        with open(query_max_freq, 'rb') as fp:
            content = fp.read()
        msg = 'max freq are not the same as highest frequency <{0}>'
        self.verify(expected_freq in content, msg.format(expected_freq))
        query_min_freq = os.path.join(
            self.output_path, os.path.basename(self.query_min_freq))
        with open(query_min_freq, 'rb') as fp:
            content = fp.read()
        msg = 'min freq are not the same as highest frequency <{0}>'
        self.verify(expected_freq in content, msg.format(expected_freq))
        msg = 'core <{0}>: max freq/min_freq/expected freq<{1}> are the same'
        self.logger.info(msg.format(core_index, expected_freq))

    def check_no_train(self):
        output = self.dut.get_session_output(timeout=2)
        msg = 'training steps should not be executed'
        self.verify('POWER: Training is Complete' not in output, msg)

    def verify_train_mode(self):
        except_content = None
        # begin run vm power policy testing
        try:
            self.start_l3fwd_power(self.check_core)
            if self.train_mode == self.NOTRAIN:
                self.check_no_train()
            else:
                # Injected Rate(64B, dst_ip=1.1.1.1):
                #      10G -> 0.1G -> 10G -> 0.1G -> 10G -> 0.1G
                check_item = [
                    [100, self.HIGH],
                    [1, self.MED],
                    [100, self.HIGH],
                    [1, self.MED],
                    [100, self.HIGH],
                    [1, self.MED], ]
                msg = '{0} begin test mode <{1}> with traffic rate percent {2}%'
                for rate, mode in check_item:
                    self.logger.info(msg.format(self.train_mode, mode, rate))
                    self.start_query(self.check_core[1])
                    info = {
                        'stm_types': ['UDP_1'],
                        'rate': rate}
                    # run traffic
                    self.run_traffic(info)
                    time.sleep(2)
                    self.stop_query()
                    # check test result
                    self.check_core_freq_in_traffic(self.check_core[1], mode)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_l3fwd_power()

        # check verify result
        if except_content:
            raise Exception(except_content)
        else:
            msg = "test <{0}> successful !!!".format(self.train_mode)
            self.logger.info(msg)

    def verify_power_driver(self):
        expected_drv = 'intel_pstate'
        power_drv = self.get_sys_power_driver()
        msg = "{0} should work with {1} driver on DUT".format(
            self.suite_name, expected_drv)
        self.verify(power_drv == expected_drv, msg)

    def preset_test_environment(self):
        self.check_core = [1, 2]
        # modprobe msr module to let the application can get the CPU HW info
        self.d_a_con('modprobe msr')
        # init binary
        self.init_l3fwd_power()
        self.init_query_script()
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify_power_driver()
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
