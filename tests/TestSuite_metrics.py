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
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
DPDK Test suite.
'''

import os
import re
import time
import random
import traceback
from copy import deepcopy
from pprint import pformat

from test_case import TestCase
from pmd_output import PmdOutput
from exception import VerifyFailure
from settings import HEADER_SIZE
from packet import Packet
from pktgen import TRANSMIT_CONT
from config import SuiteConf


class TestMetrics(TestCase):
    BIT_RATE = 'bit_rate'
    LATENCY = 'latency'
    display_seq = {
        # metrics bit rate
        BIT_RATE: [
            'mean_bits_in',
            'peak_bits_in',
            'ewma_bits_in',
            'mean_bits_out',
            'peak_bits_out',
            'ewma_bits_out'],
        # metrics latency
        LATENCY: [
            'min_latency_ns',
            'max_latency_ns',
            'avg_latency_ns',
            'jitter_ns'], }

    def d_a_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, (str, unicode)) else cmd
        output = self.dut.alt_session.send_expect(*_cmd)
        output2 = self.dut.alt_session.session.get_session_before(2)
        return output + os.linesep + output2

    @property
    def target_dir(self):
        # get absolute directory of target source code
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    def get_pkt_len(self, pkt_type, frame_size=64):
        headers_size = sum(
            map(lambda x: HEADER_SIZE[x], ['eth', 'ip', pkt_type]))
        pktlen = frame_size - headers_size
        return pktlen

    def config_stream(self, framesize):
        payload_size = self.get_pkt_len('udp', framesize)
        # set streams for traffic
        pkt_config = {
            'type': 'UDP',
            'pkt_layers': {
                'raw': {'payload': ['58'] * payload_size}}, }
        # create packet for send
        pkt_type = pkt_config.get('type')
        pkt_layers = pkt_config.get('pkt_layers')
        pkt = Packet(pkt_type=pkt_type)
        for layer in pkt_layers.keys():
            pkt.config_layer(layer, pkt_layers[layer])
        self.logger.debug(pformat(pkt.pktgen.pkt.command()))

        return pkt.pktgen.pkt

    def add_stream_to_pktgen(self, txport, rxport, send_pkt, option):
        stream_ids = []
        for pkt in send_pkt:
            _option = deepcopy(option)
            _option['pcap'] = pkt
            # link peer 0
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
            # link peer 1
            stream_id = self.tester.pktgen.add_stream(rxport, txport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def send_packets_by_pktgen(self, option):
        txport = option.get('tx_intf')
        rxport = option.get('rx_intf')
        rate = option.get('rate', float(100))
        send_pkt = option.get('stream')
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # attach streams to pktgen
        stream_option = {
            'stream_config': {
                'txmode': {},
                'transmit_mode': TRANSMIT_CONT,
                'rate': rate, }
        }
        stream_ids = self.add_stream_to_pktgen(
            txport, rxport, send_pkt, stream_option)
        # run pktgen traffic
        traffic_opt = option.get('traffic_opt')
        self.logger.debug(traffic_opt)
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)

        return result

    def run_traffic(self, option):
        tester_tx_port_id = self.tester.get_local_port(self.dut_ports[0])
        tester_rx_port_id = self.tester.get_local_port(self.dut_ports[1])
        ports_topo = {
            'tx_intf': tester_tx_port_id,
            'rx_intf': tester_rx_port_id,
            'stream': option.get('stream'),
            'rate': option.get('rate') or 100.0,
            'traffic_opt': option.get('traffic_opt'), }
        # begin traffic
        result = self.send_packets_by_pktgen(ports_topo)

        return result

    def init_testpmd(self):
        self.testpmd = PmdOutput(self.dut)

    def start_testpmd(self, mode):
        table = {
            self.BIT_RATE: 'bitrate-stats',
            self.LATENCY: 'latencystats', }
        if mode not in table:
            return
        option = '--{0}={1}'.format(table.get(mode), self.monitor_cores)
        self.testpmd.start_testpmd(
            '1S/2C/1T',
            eal_param='-v',
            param=option)
        self.is_pmd_on = True

    def set_testpmd(self):
        cmds = [
            'set fwd io',
            'start']
        [self.testpmd.execute_cmd(cmd) for cmd in cmds]

    def close_testpmd(self):
        if not self.is_pmd_on:
            return
        self.testpmd.quit()
        self.is_pmd_on = False

    def init_proc_info_tool(self):
        option = ' -v -- --metrics'
        self.dpdk_proc = os.path.join(
            self.target_dir, self.target, "app", "dpdk-procinfo" + option)
        self.metrics_stat = []

    def proc_info_query(self, flag=None):
        msg = self.d_a_con(self.dpdk_proc)
        self.logger.debug(msg)
        portStatus = {}
        keys = self.display_seq.get(flag or self.BIT_RATE)
        curPortNo = None
        portPat = r"metrics for port (\d)+.*#"
        summary = 'non port'
        for item2 in msg.splitlines():
            item = item2.strip(os.linesep)
            if 'metrics' in item:
                curPortNo = summary \
                    if summary in item.lower() else \
                    int("".join(re.findall(portPat, item, re.M)))
                portStatus[curPortNo] = {}
            if curPortNo is None:
                continue
            if ":" in item:
                status = item.strip().split(': ')
                if len(status) == 2:
                    portStatus[curPortNo][status[0]] = int(status[1].strip())
        retPortStatus = {}
        for port_id in portStatus:
            retPortStatus[port_id] = {}
            for key in keys:
                retPortStatus[port_id][key] = portStatus[port_id][key]
        self.logger.debug(pformat(retPortStatus))

        return retPortStatus

    def proc_info_query_bit_rate(self):
        self.metrics_stat.append(self.proc_info_query(self.BIT_RATE))

    def proc_info_query_latency(self):
        self.metrics_stat.append(self.proc_info_query(self.LATENCY))

    def display_suite_result(self, data):
        values = data.get('values')
        title = data.get('title')
        self.result_table_create(title)
        for value in values:
            self.result_table_add(value)
        self.result_table_print()

    def display_metrics_data(self, port_status, mode=None):
        mode = mode if mode else self.BIT_RATE
        display_seq = self.display_seq.get(mode)
        textLength = max(map(lambda x: len(x), display_seq))
        for port in sorted(port_status.keys()):
            port_value = port_status[port]
            if port != 'non port':
                self.logger.info("port {0}".format(port))
                for key in display_seq:
                    value = port_value[key]
                    self.logger.info("{0} = [{1}]".format(
                        key.ljust(textLength), value))
            else:
                maxvalue = max(map(lambda x: int(x), port_value.values()))
                if not maxvalue:
                    continue
                self.logger.info("port {0}".format(port))
                for key in display_seq:
                    value = port_value[key]
                    if value:
                        self.logger.info("{0} = [{1}]".format(
                            key.ljust(textLength), value))

    def sample_bit_rate_after_stop_traffic(self, query_interval):
        self.logger.info("sample data after stop traffic")
        max_query_count = self.query_times_after_stop
        bit_rate_stop_results = []
        while max_query_count:
            time.sleep(query_interval)
            bit_rate_stop_results.append(self.proc_info_query(self.BIT_RATE))
            max_query_count -= 1
        # get statistic after stop testpmd
        self.testpmd.execute_cmd('stop')
        stop_testpmd_results = []
        max_query_count = 2
        while max_query_count:
            time.sleep(query_interval)
            stop_testpmd_results.append(self.proc_info_query(self.BIT_RATE))
            max_query_count -= 1
        # check metrics status
        first_result = stop_testpmd_results[0]
        second_result = stop_testpmd_results[1]
        if cmp(first_result, second_result) == 0:
            msg = "bit rate statistics stop successful after stop testpmd"
            self.logger.info(msg)
        else:
            msg = "bit rate statistics fail to stop after stop testpmd"
            self.logger.warning(msg)
        return bit_rate_stop_results

    def sample_bit_rate(self, frame_size, content):
        duration = content.get('duration')
        sample_number = content.get('sample_number')
        query_interval = duration / sample_number
        # start testpmd
        self.testpmd.execute_cmd('start')
        # run traffic
        self.metrics_stat = []
        opt = {
            'stream': self.streams.get(frame_size),
            'traffic_opt': {
                'method': 'throughput',
                'duration': duration,
                'interval': query_interval,
                'callback': self.proc_info_query_bit_rate}, }
        result = self.run_traffic(opt)
        pktgen_results = [{'total': {'rx_bps': rx_pps, 'rx_pps': rx_bps}}
                          for rx_pps, rx_bps in result]
        # get data after traffic stop
        metrcis_stats_after_stop = self.sample_bit_rate_after_stop_traffic(
            query_interval)
        # save testing configuration
        sub_stats = {
            'pktgen_stats_on_traffic': pktgen_results,
            'metrics_stats_on_traffic': deepcopy(self.metrics_stat),
            'metrics_stats_after_traffic_stop': metrcis_stats_after_stop,
            'test_content': {
                'frame_size': frame_size,
                'traffic_duration': duration,
                'query_interval': query_interval}}

        return sub_stats

    def display_metrics_bit_rate(self, metrics_data):
        title = ['No', 'port']
        values = []
        for index, result in enumerate(metrics_data):
            for port, data in sorted(result.iteritems()):
                _value = [index, port]
                for key, value in data.iteritems():
                    if key not in title:
                        title.append(key)
                    _value.append(value)
                values.append(_value)
        metrics_data = {
            'title': title,
            'values': values}
        self.display_suite_result(metrics_data)

    def calculate_bit_rate_deviation(self, pktgen_stats, metrics_stats):
        pktgen_bps = max([result.get('total').get('rx_bps')
                          for result in pktgen_stats])
        metrics_bps_in = 0
        metrics_bps_out = 0
        for index, result in enumerate(metrics_stats):
            for port_id in self.dut_ports:
                metrics_bps_in += result.get(port_id).get('mean_bits_in')
                metrics_bps_out += result.get(port_id).get('mean_bits_out')
        mean_metrics_bps_in = metrics_bps_in / (index + 1)
        mean_metrics_bps_out = metrics_bps_out / (index + 1)

        return (1.0 - float(mean_metrics_bps_in) / float(pktgen_bps),
                1.0 - float(mean_metrics_bps_out) / float(pktgen_bps))

    def check_metrics_data_after_stop_traffic(self, data):
        # check mean_bits, it should be zero
        for port_id in self.dut_ports:
            for result in data:
                metrics_bps_in = result.get(port_id).get('mean_bits_in')
                metrics_bps_out = result.get(port_id).get('mean_bits_out')
                if metrics_bps_in or metrics_bps_out:
                    msg = 'mean_bits bps is not cleared as exepected'
                    raise VerifyFailure(msg)
        # check peak_bits, it should be the same
        for port_id in self.dut_ports:
            peak_bits_in = []
            peak_bits_out = []
            for result in data:
                peak_bits_in.append(result.get(port_id).get('peak_bits_in'))
                peak_bits_out.append(result.get(port_id).get('peak_bits_out'))
            if len(set(peak_bits_in)) > 1 or len(set(peak_bits_out)) > 1:
                msg = 'peak_bits bps is not keep the maximum value'
                raise VerifyFailure(msg)
        # check ewma_bits, it should decrease step by step
        for port_id in self.dut_ports:
            for key in ['ewma_bits_in', 'ewma_bits_out']:
                ewma_bits = []
                for result in data:
                    ewma_bits.append(result.get(port_id).get(key))
                status = [ewma_bits[index] > ewma_bits[port_id + 1]
                          for index in range(len(ewma_bits) - 1)]
                if all(status):
                    continue
                msg = 'ewma_bits bps not decrease'
                raise VerifyFailure(msg)

    def check_one_bit_rate_deviation(self, data, bias):
        # display test content
        test_content = data.get('test_content')
        test_cfg = {
            'title': test_content.keys(),
            'values': [test_content.values()]}
        self.display_suite_result(test_cfg)
        # display pktgen bit rate statistics on traffic
        self.logger.info("pktgen bit rate statistics:")
        pktgen_results = data.get('pktgen_stats_on_traffic')
        self.display_metrics_bit_rate(pktgen_results)
        # display metrics bit rate statistics on traffic
        self.logger.info("dpdk metrics bit rate statistics on traffic:")
        metrics_results = data.get('metrics_stats_on_traffic')
        self.display_metrics_bit_rate(metrics_results)
        # check bit rate bias between packet generator and dpdk metircs
        in_bias, out_bias = \
            self.calculate_bit_rate_deviation(pktgen_results, metrics_results)
        msg = ('in bps bias is {0} '
               'out bps bias is {1} '
               'expected bias is {2}').format(in_bias, out_bias, bias)
        self.logger.info(msg)
        if in_bias > bias or out_bias > bias:
            msg = ('metrics mean_bits bps has more than {} bias'
                   'compared with pktgen bps').format(bias)
            raise VerifyFailure(msg)
        # display dpdk metrics bit rate statistics after stop traffic
        self.logger.info("dpdk metrics bit rate statistics when stop traffic:")
        metrics_results = data.get('metrics_stats_after_traffic_stop')
        self.display_metrics_bit_rate(metrics_results)
        # check metrics tool mean_bits/ewma_bits/peak_bits behavior after stop
        # traffic
        self.check_metrics_data_after_stop_traffic(metrics_results)

    def sample_bit_rate_peak_after_stop_traffic(self, query_interval):
        self.logger.info("sample data after stop traffic")
        # sample data after stop
        max_query_count = self.query_times_after_stop
        bit_rate_stop_results = []
        while max_query_count:
            time.sleep(query_interval)
            bit_rate_stop_results.append(self.proc_info_query(self.BIT_RATE))
            max_query_count -= 1
        # check metrics status after stop testpmd
        self.testpmd.execute_cmd('stop')
        self.logger.info("get metrics bit rate stop after stop testpmd:")
        stop_testpmd_results = []
        max_query_count = 2
        while max_query_count:
            time.sleep(query_interval)
            stop_testpmd_results.append(self.proc_info_query(self.BIT_RATE))
            max_query_count -= 1
        # check metrics tool status
        first_result = stop_testpmd_results[0]
        second_result = stop_testpmd_results[1]
        if cmp(first_result, second_result) == 0:
            msg = "metrics bit rate stop successful after stop testpmd"
            self.logger.info(msg)
        else:
            msg = "metrics bit rate fail to stop after stop testpmd"
            self.logger.warning(msg)
        return bit_rate_stop_results

    def sample_bit_rate_peak(self, frame_size, rate, content):
        duration = content.get('duration')
        sample_number = content.get('sample_number')
        query_interval = duration / sample_number
        # start testpmd
        self.testpmd.execute_cmd('start')
        # run traffic
        opt = {
            'stream': self.streams.get(frame_size),
            'rate': rate,
            'traffic_opt': {
                'method': 'throughput',
                'duration': duration, }, }
        result = self.run_traffic(opt)
        pktgen_results = [{'total': {'rx_bps': rx_pps, 'rx_pps': rx_bps}}
                          for rx_pps, rx_bps in [result]]
        # get data after traffic stop
        metrcis_stats_after_stop = \
            self.sample_bit_rate_peak_after_stop_traffic(query_interval)
        # save testing configuration
        sub_stats = {
            'pktgen_stats_on_traffic': pktgen_results,
            'metrics_stats_after_traffic_stop': metrcis_stats_after_stop,
            'test_content': {
                'rate': rate,
                'frame_size': frame_size,
                'traffic_duration': duration,
                'query_interval': query_interval}}

        return sub_stats

    def get_one_bit_rate_peak(self, data):
        # display test content
        test_content = data.get('test_content')
        test_cfg = {
            'title': test_content.keys(),
            'values': [test_content.values()]}
        self.display_suite_result(test_cfg)
        # display pktgen bit rate statistics on traffic
        self.logger.info("pktgen bit rate statistics :")
        pktgen_results = data.get('pktgen_stats_on_traffic')
        self.display_metrics_bit_rate(pktgen_results)
        pktgen_bps = max([result.get('total').get('rx_bps')
                          for result in pktgen_results])
        # display dpdk metrics bit rate statistics after stop traffic
        self.logger.info("dpdk bit rate statistics after stop traffic:")
        metrics_results = data.get('metrics_stats_after_traffic_stop')
        self.display_metrics_bit_rate(metrics_results)
        metrics_peak_data = {}
        for port_id in self.dut_ports:
            metrics_peak_data[port_id] = {
                'peak_bits_in':
                max([result.get(port_id).get('peak_bits_in')
                     for result in metrics_results]),
                'peak_bits_out':
                max([result.get(port_id).get('peak_bits_out')
                     for result in metrics_results]),
            }
        return pktgen_bps, metrics_peak_data

    def check_bit_rate_peak_data(self, data):
        '''
        check ``peak_bits_in/peak_bits_out`` should keep the first max value
        when packet generator work with decreasing traffic rate percent.
        '''
        pktgen_stats = []
        metrics_stats = []
        for sub_data in data:
            pktgen_stat, metrics_stat = self.get_one_bit_rate_peak(sub_data)
            pktgen_stats.append(pktgen_stat)
            metrics_stats.append(metrics_stat)
        # check if traffic run with decreasing rate percent
        status = [pktgen_stats[index] > pktgen_stats[index + 1]
                  for index in range(len(pktgen_stats) - 1)]
        msg = 'traffic rate percent does not run with decreasing rate percent'
        self.verify(all(status), msg)
        # check ``peak_bits_in/peak_bits_out`` keep the first max value
        for port_id in self.dut_ports:
            for key in ['peak_bits_in', 'peak_bits_out']:
                peak_values = [metrics_stat.get(port_id).get(key)
                               for metrics_stat in metrics_stats]
                max_value = max(peak_values)
                if max_value != metrics_stats[0].get(port_id).get(key):
                    msg = 'port {0} {1} does not keep maximum value'.format(
                        port_id, key)
                    raise VerifyFailure(msg)

    def sample_latency_after_stop_traffic(self, query_interval):
        self.logger.info("sample statistics after stop traffic")
        # sample data after stop
        max_query_count = self.query_times_after_stop
        latency_stop_results = []
        while max_query_count:
            time.sleep(5)
            latency_stop_results.append(self.proc_info_query(self.LATENCY))
            max_query_count -= 1
        # check statistic status after stop testpmd
        self.testpmd.execute_cmd('stop')
        self.logger.info("query metrics latency after stop testpmd:")
        stop_testpmd_results = []
        max_query_count = 2
        while max_query_count:
            time.sleep(query_interval)
            stop_testpmd_results.append(self.proc_info_query(self.LATENCY))
            max_query_count -= 1
        # check metrics behavior
        first_result = stop_testpmd_results[0]
        second_result = stop_testpmd_results[1]
        if cmp(first_result, second_result) == 0:
            msg = "metrics latency stop successful after stop testpmd"
            self.logger.info(msg)
        else:
            msg = "metrics latency fail to stop after stop testpmd"
            self.logger.warning(msg)
        return latency_stop_results

    def display_metrics_latency(self, metrics_data):
        title = ['No', 'port']
        values = []
        for index, result in enumerate(metrics_data):
            for port_id, data in result.iteritems():
                _value = [index, port_id]
                for key, value in data.iteritems():
                    if key not in title:
                        title.append(key)
                    _value.append(value)
                values.append(_value)
        metrics_data = {
            'title': title,
            'values': values}
        self.display_suite_result(metrics_data)

    def sample_latency(self, frame_size, content):
        self.metrics_stat = []
        duration = content.get('duration')
        sample_number = content.get('sample_number')
        query_interval = duration / sample_number
        # start testpmd
        self.testpmd.execute_cmd('start')
        # run traffic
        opt = {
            'stream': self.streams.get(frame_size),
            'traffic_opt': {
                'method': 'latency',
                'duration': duration, }, }
        pktgen_results = self.run_traffic(opt)
        # get data after traffic stop
        metrcis_stats_after_stop = self.sample_latency_after_stop_traffic(
            query_interval)
        # save testing configuration and results
        sub_stats = {
            'pktgen_stats_on_traffic': pktgen_results,
            'metrics_stats_after_traffic_stop': metrcis_stats_after_stop,
            'test_content': {
                'rate': 100.0,
                'frame_size': frame_size,
                'traffic_duration': duration,
                'query_interval': query_interval}}

        return sub_stats

    def check_one_latecny_data(self, data):
        '''
        packet generator calculates line latency between tx port and rx port,
        dpdk metrics calculates packet forward latency between rx and tx inside
        testpmd. These two types latency data are used for different purposes.
        '''
        # display test content
        test_content = data.get('test_content')
        test_cfg = {
            'title': test_content.keys(),
            'values': [test_content.values()]}
        self.display_suite_result(test_cfg)
        # display pktgen latency statistics on traffic
        self.logger.info("pktgen line latency statistics :")
        pktgen_results = data.get('pktgen_stats_on_traffic')
        self.display_metrics_latency([pktgen_results])
        # check if the value is reasonable, no reference data
        for port, value in pktgen_results.iteritems():
            max_value = value.get('max')
            min_value = value.get('min')
            average = value.get('average')
            if max_value == 0 and average == 0 and min_value == 0:
                msg = 'failed to get pktgen latency data'
                raise VerifyFailure(msg)
                continue
            if max_value > average and average > min_value and min_value > 0:
                continue
            msg = ('pktgen latency is wrong: '
                   'max <{0}> '
                   'average <{1}> '
                   'min <{2}>').format(
                max_value, average, min_value)
            raise VerifyFailure(msg)
        # display dpdk metrics latency statistics
        self.logger.info("dpdk forward latency statistics :")
        metrics_results = data.get('metrics_stats_after_traffic_stop')
        self.display_metrics_latency(metrics_results)
        # check if the value is reasonable, no reference data
        for index, result in enumerate(metrics_results):
            for port, value in result.iteritems():
                if port != 'non port':
                    continue
                max_value = value.get('max_latency_ns')
                min_value = value.get('min_latency_ns')
                average = value.get('avg_latency_ns')
                # ignore invalid data
                if max_value == 0 and average == 0 and min_value == 0:
                    msg = 'failed to get metrics latency data'
                    raise VerifyFailure(msg)
                if max_value > average and \
                   average > min_value and min_value > 0:
                    continue
                msg = ('metrics latency is wrong : '
                       'min_latency_ns <{0}> '
                       'avg_latency_ns <{1}> '
                       'min_latency_ns <{2}>').format(
                    max_value, average, min_value)
                raise VerifyFailure(msg)
        msg = 'frame_size {0} latency data is ok.'.format(
            test_content.get('frame_size'))
        self.logger.info(msg)

    def verify_bit_rate(self):
        except_content = None
        try:
            # set testpmd on ready status
            self.start_testpmd(self.BIT_RATE)
            self.set_testpmd()
            stats = []
            for frame_size in self.test_content.get('frame_sizes'):
                sub_stats = self.sample_bit_rate(frame_size, self.test_content)
                stats.append(
                    [sub_stats, self.test_content.get('bias').get(frame_size)])
            for data, bias in stats:
                self.check_one_bit_rate_deviation(data, bias)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise Exception(except_content)

    def verify_bit_rate_peak(self):
        except_content = None
        try:
            # set testpmd on ready status
            self.start_testpmd(self.BIT_RATE)
            self.set_testpmd()
            stats = []
            frame_sizes = self.test_content.get('frame_sizes')
            frame_size = frame_sizes[random.randint(0, len(frame_sizes) - 1)]
            for rate in self.test_content.get('rates'):
                sub_stats = self.sample_bit_rate_peak(
                    frame_size, rate, self.test_content)
                stats.append(sub_stats)
            self.check_bit_rate_peak_data(stats)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise Exception(except_content)

    def verify_latency_stat(self):
        except_content = None
        try:
            # set testpmd on ready status
            self.start_testpmd(self.LATENCY)
            self.set_testpmd()
            # get test content
            stats = []
            for frame_size in self.test_content.get('frame_sizes'):
                sub_stats = self.sample_latency(frame_size, self.test_content)
                stats.append(sub_stats)
            for data in stats:
                self.check_one_latecny_data(data)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.close_testpmd()

        # re-raise verify exception result
        if except_content:
            raise Exception(except_content)

    def verify_supported_nic(self):
        supported_drivers = ['ixgbe']
        result = all([self.dut.ports_info[port_id]['port'].default_driver in
                      supported_drivers
                      for port_id in self.dut_ports])
        msg = "current nic is not supported"
        self.verify(result, msg)

    def get_test_content_from_cfg(self):
        conf = SuiteConf(self.suite_name)
        cfg_content = dict(conf.suite_conf.load_section('content'))
        frames_cfg = cfg_content.get('frames_cfg')
        info = [(int(item[0]), float(item[1]))
                for item in [item.split(':') for item in frames_cfg.split(',')]]
        frames_info = dict(info)
        test_content = {
            'frame_sizes': frames_info.keys(),
            'duration': int(cfg_content.get('duration') or 0),
            'sample_number': int(cfg_content.get('sample_number') or 0),
            'rates': [int(item)
                      for item in cfg_content.get('rates').split(',')],
            'bias': frames_info}
        self.query_times_after_stop = 5

        return test_content

    def preset_traffic(self):
        self.streams = {}
        # prepare streams instance
        for frame_size in self.test_content.get('frame_sizes'):
            self.streams[frame_size] = self.config_stream(frame_size)

    def preset_test_environment(self):
        # get test content
        self.test_content = self.get_test_content_from_cfg()
        self.logger.debug(pformat(self.test_content))
        # binary status flag
        self.is_pmd_on = None
        # monitor cores
        self.monitor_cores = '2'
        # init binary
        self.init_testpmd()
        self.init_proc_info_tool()
        # traffic relevant
        self.preset_traffic()
    #
    # Test cases.
    #

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Not enough ports")
        # prepare testing environment
        self.preset_test_environment()

    def tear_down_all(self):
        """ Run after each test suite. """
        pass

    def set_up(self):
        """ Run before each test case. """
        pass

    def tear_down(self):
        """ Run after each test case. """
        self.dut.kill_all()

    def test_perf_bit_rate_peak(self):
        """
        Test bit rate peak
        """
        self.verify_bit_rate_peak()

    def test_perf_bit_rate(self):
        """
        Test bit rate
        """
        self.verify_bit_rate()

    def test_perf_latency_stat(self):
        """
        Test latency stat
        """
        self.verify_latency_stat()
