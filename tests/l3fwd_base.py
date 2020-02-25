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
Layer-3 forwarding test script base class.
"""
import os
import time
import traceback
import texttable
import json
from pprint import pformat
from itertools import product
from copy import deepcopy

from config import SuiteConf
from settings import HEADER_SIZE
from packet import Packet
from pktgen import TRANSMIT_CONT, PKTGEN_TREX, PKTGEN_IXIA
from utils import convert_int2ip, convert_ip2int
from exception import VerifyFailure
import utils


# LPM(longest prefix match) mode
LPM = 'lpm'
# EM(Exact-Match) mode
EM = 'em'
# stream types
L3_IPV6 = 'ipv6'
L3_IPV4 = 'ipv4'


class L3fwdBase(object):

    def l3fwd_init(self, valports, socket):
        self.__valports = valports
        self.__white_list = None
        self.__socket = socket
        self.__nic_name = self.nic
        self.__pkt_typ = 'udp'
        # for result
        self.__cur_case = None
        self.__json_results = {}

    @property
    def output_path(self):
        suiteName = self.suite_name
        if self.logger.log_path.startswith(os.sep):
            output_path = os.path.join(self.logger.log_path, suiteName)
        else:
            cur_path = os.sep.join(
                os.path.realpath(__file__).split(os.sep)[:-2])
            output_path = os.path.join(
                cur_path, self.logger.log_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        return output_path

    def d_con(self, cmd):
        _cmd = [cmd, '# ', 10] if isinstance(cmd, (str)) else cmd
        return self.dut.send_expect(*_cmd)

    def __get_ipv4_lpm_vm_config(self, lpm_config):
        netaddr, mask = lpm_config.split('/')
        ip_range = int('1' * (32 - int(mask)), 2)
        start_ip = convert_int2ip(convert_ip2int(netaddr) + 1)
        end_ip = convert_int2ip(convert_ip2int(start_ip) + ip_range - 1)
        layers = {'ipv4': {'src': start_ip, }, }
        fields_config = {
            'ip': {'dst': {
                'src': start_ip,
                'dst': end_ip,
                'step': 1,
                'action': 'random', }, }, }
        return layers, fields_config

    def __get_ipv6_lpm_vm_config(self, lpm_config):
        netaddr, mask = lpm_config.split('/')
        ip_range = int('1' * (128 - int(mask)), 2)
        start_ip = convert_int2ip(
            convert_ip2int(netaddr, ip_type=6) + 1, ip_type=6)
        end_ip = convert_int2ip(
            convert_ip2int(start_ip, ip_type=6) + ip_range - 1, ip_type=6)
        layers = {'ipv6': {'src': start_ip, }, }
        fields_config = {
            'ipv6': {'dst': {
                'src': start_ip,
                'dst': end_ip,
                'step': 1,
                'action': 'random', }, }, }
        return layers, fields_config

    def __get_pkt_len(self, pkt_type, ip_type='ip', frame_size=64):
        headers_size = sum(
            map(lambda x: HEADER_SIZE[x], ['eth', ip_type, pkt_type]))
        pktlen = frame_size - headers_size
        return pktlen

    def __get_frame_size(self, name, frame_size):
        _frame_size = 66 if name == L3_IPV6 and frame_size == 64 else \
            frame_size
        return _frame_size

    def __config_stream(self, stm_name, layers=None, frame_size=64):
        _framesize = self.__get_frame_size(stm_name, frame_size)
        payload_size = self.__get_pkt_len(
            self.__pkt_typ,
            'ip' if stm_name == L3_IPV4 else 'ipv6', _framesize)
        # set streams for traffic
        pkt_configs = {
            L3_IPV4: {
                'type': self.__pkt_typ.upper(),
                'pkt_layers': {
                    'raw': {'payload': ['58'] * payload_size}}},
            L3_IPV6: {
                'type': 'IPv6_' + self.__pkt_typ.upper(),
                'pkt_layers': {
                    'raw': {'payload': ['58'] * payload_size}}}, }
        if stm_name not in pkt_configs.keys():
            msg = '{} not set in table'.format(stm_name)
            raise VerifyFailure(msg)
        values = deepcopy(pkt_configs.get(stm_name))
        if layers:
            values['pkt_layers'].update(layers)
        self.logger.debug(pformat(values))
        pkt = self.__get_pkt_inst(values)

        return pkt

    def __get_pkt_inst(self, pkt_config):
        pkt_type = pkt_config.get('type')
        pkt_layers = pkt_config.get('pkt_layers')
        pkt = Packet(pkt_type=pkt_type)
        for layer in pkt_layers.keys():
            pkt.config_layer(layer, pkt_layers[layer])
        self.logger.debug(pformat(pkt.pktgen.pkt.command()))

        return pkt.pktgen.pkt

    def __preset_flows_configs(self):
        flows = self.__test_content.get('flows')
        if not flows:
            msg = "flows not set in json cfg file"
            raise VerifyFailure(msg)
        flows_configs = {}
        for name, mode_configs in flows.items():
            for mode, configs in mode_configs.items():
                for index, config in enumerate(configs):
                    if mode == LPM:
                        # under LPM mode, one port only set one stream
                        if index >= len(self.__valports):
                            break
                        port_id = self.__valports[index]
                        dmac = self.dut.get_mac_address(port_id)
                        _layer = {'ether': {'dst': dmac, }, }
                        _layer2, fields_config = \
                            self.__get_ipv4_lpm_vm_config(config) \
                            if name == L3_IPV4 else \
                            self.__get_ipv6_lpm_vm_config(config)
                        _layer.update(_layer2)
                    else:
                        if index >= 2 * len(self.__valports):
                            break
                        port_id = \
                            self.__valports[int(index / 2) % len(self.__valports)]
                        dmac = self.dut.get_mac_address(port_id)
                        _layer = {'ether': {'dst': dmac, }, }
                        _layer.update(config)
                        fields_config = None
                    flows_configs.setdefault((name, mode), []).append(
                        [_layer, fields_config])
        return flows_configs

    def __preset_streams(self):
        frame_sizes = self.__test_content.get('frame_sizes')
        if not frame_sizes:
            msg = "frame sizes not set in json cfg file"
            raise VerifyFailure(msg)
        test_streams = {}
        flows_configs = self.__preset_flows_configs()
        for frame_size in frame_sizes:
            for flow_key, flows_config in flows_configs.items():
                streams_key = flow_key + (frame_size, )
                for flow_config in flows_config:
                    _layers, fields_config = flow_config
                    pkt = self.__config_stream(
                        flow_key[0], _layers, frame_size)
                    test_streams.setdefault(streams_key, []).append(
                        [pkt, fields_config])
        self.logger.debug(pformat(test_streams))
        return test_streams

    def __add_stream_to_pktgen(self, streams, option):
        def port(index):
            p = self.tester.get_local_port(self.__valports[index])
            return p
        topos = [[port(index), port(index - 1)]
                 if index % 2 else
                 [port(index), port(index + 1)]
                 for index, _ in enumerate(self.__valports)] \
                 if len(self.__valports) > 1 else [[port(0), port(0)]]
        stream_ids = []
        step = int(len(streams) / len(self.__valports))
        for cnt, stream in enumerate(streams):
            pkt, fields_config = stream
            index = cnt // step
            txport, rxport = topos[index]
            _option = deepcopy(option)
            _option['pcap'] = pkt
            if fields_config:
                _option['fields_config'] = fields_config
            stream_id = self.tester.pktgen.add_stream(txport, rxport, pkt)
            self.tester.pktgen.config_stream(stream_id, _option)
            stream_ids.append(stream_id)
        return stream_ids

    def __send_packets_by_pktgen(self, option):
        streams = option.get('stream')
        rate = option.get('rate')
        # set traffic option
        traffic_opt = option.get('traffic_opt')
        self.logger.debug(option)
        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # set stream into pktgen
        stream_option = {
            'stream_config': {
                'txmode': {},
                'transmit_mode': TRANSMIT_CONT,
                'rate': rate, }}
        stream_ids = self.__add_stream_to_pktgen(streams, stream_option)
        # run packet generator
        result = self.tester.pktgen.measure(stream_ids, traffic_opt)
        return result

    def __throughput(self, l3_proto, mode, frame_size):
        """
        measure __throughput according to Layer-3 Protocol and Lookup Mode
        """
        flow_key = (l3_proto, mode, frame_size)
        if flow_key not in self.__streams.keys():
            msg = "{} {} {}: expected streams failed to create".format(
                *flow_key)
            raise VerifyFailure(msg)
        streams = self.__streams.get(flow_key)
        # set traffic option
        duration = self.__test_content.get('test_duration')
        option = {
            'stream': streams,
            'rate': 100,
            'traffic_opt': {
                'method': 'throughput',
                'duration': duration, }}
        # run traffic
        result = self.__send_packets_by_pktgen(option)
        # statistics result
        _, pps = result
        self.verify(pps > 0, "No traffic detected")
        return result

    def __rfc2544(self, config, l3_proto, mode, frame_size):
        """
        measure RFC2544 according to Layer-3 Protocol and Lookup Mode
        """
        flow_key = (l3_proto, mode, frame_size)
        if flow_key not in self.__streams.keys():
            msg = "{} {} {}: expected streams failed to create".format(
                *flow_key)
            raise VerifyFailure(msg)
        streams = self.__streams.get(flow_key)
        # set traffic option
        if not self.__cur_case:
            msg = 'current test case name not set, use default traffic option'
            self.logger.warning(msg)
        conf_opt = self.__test_content.get('expected_rfc2544', {}).get(
            self.__cur_case, {}).get(self.__nic_name, {}).get(config, {}).get(
            str(frame_size), {}).get('traffic_opt', {})
        max_rate = float(conf_opt.get('max_rate') or 100.0)
        min_rate = float(conf_opt.get('min_rate') or 0.0)
        accuracy = float(conf_opt.get('accuracy') or 0.001)
        pdr = float(conf_opt.get('pdr') or 0.001)
        duration = self.__test_content.get('test_duration')
        option = {
            'stream': streams,
            'rate': max_rate,
            'traffic_opt': {
                'method': 'rfc2544_dichotomy',
                'max_rate': max_rate,
                'min_rate': min_rate,
                'accuracy': accuracy,
                'pdr': pdr,
                'duration': duration, }}
        # run traffic
        result = self.__send_packets_by_pktgen(option)
        # statistics result
        if result:
            _, tx_pkts, rx_pkts = result
            self.verify(tx_pkts > 0, "No traffic detected")
            self.verify(rx_pkts > 0, "No packet transfer detected")
        else:
            msg = 'failed to get zero loss rate percent with traffic option.'
            self.logger.error(msg)
            self.logger.info(pformat(option))

        return result

    def __preset_compilation(self):
        # Update config file and rebuild to get best perf on FVL
        if self.nic in ["fortville_sprit", "fortville_eagle", "fortville_25g"]:
            self.d_con(
                ("sed -i -e 's/"
                 "CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=n/"
                 "CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=y/' "
                 "./config/common_base"))
            self.dut.build_install_dpdk(self.target)
        # init l3fwd binary file
        self.logger.info(
            "Configure RX/TX descriptor to 2048, re-build ./examples/l3fwd")
        self.d_con((
            "sed -i -e 's/"
            "define RTE_TEST_RX_DESC_DEFAULT.*$/"
            "define RTE_TEST_RX_DESC_DEFAULT 2048/' "
            "./examples/l3fwd/l3fwd.h"))
        self.d_con((
            "sed -i -e 's/"
            "define RTE_TEST_TX_DESC_DEFAULT.*$/"
            "define RTE_TEST_TX_DESC_DEFAULT 2048/' "
            "./examples/l3fwd/l3fwd.h"))
        self.__l3fwd_em = self.__init_l3fwd(EM)
        self.__l3fwd_lpm = self.__init_l3fwd(LPM)

    def __init_l3fwd(self, mode):
        """
        Prepare long prefix match table, __replace P(x) port pattern
        """
        l3fwd_method = '_'.join(['l3fwd', mode])
        self.d_con("make clean -C examples/l3fwd")
        flg = 1 if LPM in l3fwd_method else 0
        out = self.dut.build_dpdk_apps(
            "./examples/l3fwd",
            "USER_FLAGS=-DAPP_LOOKUP_METHOD={}".format(flg))
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")
        # rename binary file
        self.d_con(
            ("mv -f examples/l3fwd/build/l3fwd "
             "examples/l3fwd/build/{}").format(l3fwd_method))
        l3fwd_bin = os.path.join("./examples/l3fwd/build/", l3fwd_method)
        return l3fwd_bin

    def __start_l3fwd(self, mode, core_mask, config, frame_size):
        bin = self.__l3fwd_em if mode == EM else self.__l3fwd_lpm
        # Start L3fwd application
        command_line = (
            "{bin} "
            "-c {cores} "
            "-n {channel} "
            "{whitelist}"
            "-- "
            "-p {port_mask} "
            "--config '{config}'"
            "").format(**{
                'bin': bin,
                'cores': core_mask,
                'channel': self.dut.get_memory_channels(),
                'whitelist': self.__white_list if self.__white_list else '',
                'port_mask': utils.create_mask(self.__valports),
                'config': config, })
        if self.nic == "niantic":
            command_line += " --parse-ptype"
        if frame_size > 1518:
            command_line += " --enable-jumbo --max-pkt-len %d" % frame_size
        self.d_con([command_line, "L3FWD:", 120])
        self.__is_l3fwd_on = True
        # wait several second for l3fwd checking ports link status.
        # It is aimed to make sure trex detect link up status.
        time.sleep(2 * len(self.__valports))

    def __close_l3fwd(self):
        if not self.__is_l3fwd_on:
            return
        self.d_con("^C")
        self.__is_l3fwd_on = False

    def __json_rfc2544(self, value):
        return {"unit": "Mpps", "name": "Rfc2544",
                "value": value[0], "delta": value[1]}

    def __json_throughput(self, value):
        return {"unit": "Mpps", "name": "Throughput",
                "value": value[0], "delta": value[1]}

    def __json_line_rate(self, value):
        return {"unit": "", "name": "% of Line Rate", "value": value}

    def __json_port_config(self, value):
        return {"unit": "", "name": "Number of Cores/Queues/Threads",
                "value": value}

    def __json_frame_size(self, value):
        return {"unit": "bytes", "name": "Frame size",
                "value": value}

    def __save_throughput_result(self, case_name, result):
        suite_results = {}
        case_result = suite_results[case_name] = []
        for sub_result in result:
            status, throughput, line_rate, port_config, frame_size = sub_result
            one_result = {
                "status": status,
                "performance": [
                    self.__json_throughput(throughput),
                    self.__json_line_rate(line_rate), ],
                "parameters": [
                    self.__json_port_config(port_config),
                    self.__json_frame_size(frame_size), ]}
            case_result.append(one_result)
        self.logger.debug(pformat(suite_results))
        self.__json_results[case_name] = suite_results

    def __save_rfc2544_result(self, case_name, result):
        suite_results = {}
        case_result = suite_results[case_name] = []
        for sub_result in result:
            status, rfc2544, line_rate, port_config, frame_size = sub_result
            one_result = {
                "status": status,
                "performance": [
                    self.__json_rfc2544(rfc2544),
                    self.__json_line_rate(line_rate), ],
                "parameters": [
                    self.__json_port_config(port_config),
                    self.__json_frame_size(frame_size), ]}
            case_result.append(one_result)
        self.logger.debug(pformat(suite_results))
        self.__json_results[case_name] = suite_results

    def l3fwd_save_results(self, json_file=None):
        if not self.__json_results:
            msg = 'json results data is empty'
            self.logger.error(msg)
            return
        _js_file = os.path.join(
            self.output_path,
            json_file if json_file else 'l3fwd_result.json')
        with open(_js_file, 'w') as fp:
            json.dump(self.__json_results, fp, indent=4,
                      separators=(',', ': '),
                      sort_keys=True)

    def __display_suite_result(self, data, mode):
        values = data.get('values')
        title = data.get('title')
        max_length = sum([len(item) + 5 for item in title])
        self.result_table_create(title)
        self._result_table.table = texttable.Texttable(max_width=max_length)
        for value in values:
            self.result_table_add(value)
        self.result_table_print()

    def __check_throughput_result(self, stm_name, data, mode):
        if not data:
            msg = 'no result data'
            raise VerifyFailure(msg)
        values = []
        js_results = []
        bias = float(self.__test_content.get('accepted_tolerance') or 1.0)
        for sub_data in data:
            config, frame_size, result = sub_data
            _, pps = result
            pps /= 1000000.0
            _frame_size = self.__get_frame_size(stm_name, frame_size)
            linerate = self.wirespeed(
                self.nic, _frame_size, len(self.__valports))
            percentage = pps * 100 / linerate
            # data for display
            values.append(
                [config, frame_size, mode.upper(), str(pps), str(percentage)])
            # check data with expected values
            expected_rate = None if not self.__cur_case else \
                self.__test_content.get('expected_throughput', {}).get(
                    self.__cur_case, {}).get(self.__nic_name, {}).get(
                        config, {}).get(str(frame_size))
            if expected_rate and float(expected_rate):
                expected = float(expected_rate)
                gap = 100 * (pps - expected) / expected
                if abs(gap) < bias:
                    status = 'pass'
                else:
                    status = 'failed'
                    msg = ('expected <{}>, '
                           'current <{}> is '
                           '{}% over accepted tolerance').format(
                        expected, pps, round(gap, 2))
                    self.logger.error(msg)
            else:
                msg = ('{0} {1} expected throughput value is not set, '
                       'ignore check').format(config, frame_size)
                self.logger.warning(msg)
                status = 'pass'
            js_results.append([status, result, linerate, config, frame_size])
        # save data with json format
        self.__save_throughput_result(self.__cur_case, js_results)
        # display result table
        title = [
            'Total Cores/Threads/Queues per port',
            'Frame Size',
            "Mode",
            'Throughput Rate {} Mode mpps'.format(mode.upper()),
            'Throughput Rate {} Mode Linerate%'.format(mode.upper()), ]

        _data = {
            'title': title,
            'values': values}
        self.__display_suite_result(_data, mode)

    def __check_rfc2544_result(self, stm_name, data, mode):
        if not data:
            msg = 'no result data'
            raise Exception(msg)
        bias = self.__test_content.get('accepted_tolerance')
        values = []
        js_results = []
        for sub_data in data:
            config, frame_size, result = sub_data
            expected_cfg = {} if not self.__cur_case else \
                self.__test_content.get('expected_rfc2544', {}).get(
                self.__cur_case, {}).get(self.__nic_name, {}).get(
                config, {}).get(str(frame_size), {})
            zero_loss_rate, tx_pkts, rx_pkts = result if result else [None] * 3
            # expected line rate
            _frame_size = self.__get_frame_size(stm_name, frame_size)
            linerate = self.wirespeed(
                self.nic, _frame_size, len(self.__valports))
            throughput = linerate * zero_loss_rate / 100
            # append data for display
            pdr = expected_cfg.get('traffic_opt', {}).get('pdr')
            values.append([
                config, frame_size, mode.upper(),
                str(throughput),
                str(zero_loss_rate),
            ])
            # check data with expected values
            expected_rate = float(expected_cfg.get('rate') or 100.0)
            status = 'pass' \
                if zero_loss_rate and zero_loss_rate > expected_rate \
                else 'failed'
            js_results.append(
                [status, [zero_loss_rate, 0], linerate, config, frame_size])
        # save data in json file
        self.__save_rfc2544_result(self.__cur_case, js_results)
        # display result table
        title = [
            'Total Cores/Threads/Queues per port',
            "Frame Size",
            "Mode",
            'Theory line rate (Mpps) '.format(mode.upper()),
            '{} Mode Zero Loss Rate % '.format(mode.upper()),
        ]

        _data = {
            'title': title,
            'values': values}
        self.__display_suite_result(_data, mode)

    def ms_throughput(self, l3_proto, mode):
        except_content = None
        try:
            test_content = self.__test_content.get('port_configs')
            results = []
            for config, core_mask, port_conf, frame_size in test_content:
                # Start L3fwd application
                self.logger.info(
                    ("Executing l3fwd with {0} mode, {1} ports, "
                     "{2} and {3} frame size").format(
                        mode, len(self.__valports), config, frame_size))
                self.__start_l3fwd(mode, core_mask, port_conf, frame_size)
                result = self.__throughput(l3_proto, mode, frame_size)
                # Stop L3fwd
                self.__close_l3fwd()
                if result:
                    results.append([config, frame_size, result])
            self.__check_throughput_result(l3_proto, results, mode)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.__close_l3fwd()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def qt_rfc2544(self, l3_proto, mode):
        except_content = None
        try:
            test_content = self.__test_content.get('port_configs')
            results = []
            for config, core_mask, port_conf, frame_size in test_content:
                # Start L3fwd application
                self.logger.info(
                    ("Executing l3fwd with {0} mode, {1} ports, "
                     "{2} and {3} frame size").format(
                        mode, len(self.__valports), config, frame_size))
                self.__start_l3fwd(mode, core_mask, port_conf, frame_size)
                result = self.__rfc2544(config, l3_proto, mode, frame_size)
                # Stop L3fwd
                self.__close_l3fwd()
                if result:
                    results.append([config, frame_size, result])
            self.__check_rfc2544_result(l3_proto, results, mode)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            except_content = e
        finally:
            self.__close_l3fwd()

        # re-raise verify exception result
        if except_content:
            raise VerifyFailure(except_content)

    def __parse_port_config(self, config):
        cores, total_threads, queue = config.split('/')
        _thread = str(int(int(total_threads[:-1]) / int(cores[:-1]))) + 'T'
        _cores = str(int(cores[:-1]) * len(self.__valports)) + 'C'
        # only use one socket
        cores_config = '/'.join(['1S', _cores, _thread])
        queues_per_port = int(queue[:-1])
        return cores_config, queues_per_port

    def __get_test_configs(self, options, ports, socket):
        if not options:
            msg = "'test_parameters' not set in suite configuration file"
            raise VerifyFailure(msg)
        configs = []
        frame_sizes_grp = []
        for test_item, frame_sizes in sorted(options.items()):
            _frame_sizes = [int(frame_size) for frame_size in frame_sizes]
            frame_sizes_grp.extend([int(item) for item in _frame_sizes])
            cores, queues_per_port = self.__parse_port_config(test_item)
            grp = [list(item)
                   for item in product(range(queues_per_port), range(ports))]
            corelist = self.dut.get_core_list(
                cores, socket if cores.startswith('1S') else -1)
            corelist = [str(int(core) + 2) for core in corelist]
            cores_mask = utils.create_mask(corelist)
            total = len(grp)
            _corelist = (corelist * (total // len(corelist) + 1))[:total]
            # ignore first 2 cores
            [grp[index].append(core)
             for index, core in enumerate(_corelist)]
            # (port,queue,lcore)
            [configs.append([
                test_item,
                cores_mask,
                ','.join(["({0},{1},{2})".format(port, queue, core)
                          for queue, port, core in grp]),
                frame_size, ]) for frame_size in _frame_sizes]
        return configs, sorted(set(frame_sizes_grp))

    def __get_test_content_from_cfg(self, test_content):
        self.logger.debug(pformat(test_content))
        # get flows configuration
        suite_conf = SuiteConf('l3fwd_base')
        flows = suite_conf.suite_cfg.get('l3fwd_flows')
        test_content['flows'] = flows
        # parse port config of l3fwd
        port_configs, frame_sizes = self.__get_test_configs(
            test_content.get('test_parameters'),
            len(self.__valports), self.__socket)
        test_content['port_configs'] = port_configs
        test_content['frame_sizes'] = frame_sizes
        self.logger.debug(pformat(test_content))

        return test_content

    def __get_whitelist(self, port_list):
        white_list = ''
        for port_index in port_list:
            pci = self.dut.ports_info[port_index].get('pci')
            if not pci:
                continue
            white_list += '-w {} '.format(pci)
        return white_list

    def __preset_port_list(self, test_content):
        port_list = test_content.get('port_list')
        if port_list:
            if not set(port_list).issubset(set(self.__valports)):
                msg = 'total ports are {}, select ports are wrong'.format(
                    pformat(self.__valports))
                raise VerifyFailure(msg)
            else:
                msg = 'current using ports {} for testing'.format(
                    pformat(port_list))
                self.logger.info(msg)
            self.__valports = port_list
            self.__white_list = self.__get_whitelist(port_list)

    def l3fwd_preset_test_environment(self, test_content):
        # if user set port list in cfg file, use
        self.__preset_port_list(test_content)
        # get test content
        self.__test_content = self.__get_test_content_from_cfg(test_content)
        # binary process flag
        self.__is_l3fwd_on = None
        # prepare target source code application
        self.__preset_compilation()
        # config streams
        self.__streams = self.__preset_streams()

    def l3fwd_set_cur_case(self, name):
        self.__cur_case = name

    def l3fwd_reset_cur_case(self):
        self.__cur_case = None

    @property
    def is_pktgen_on(self):
        return hasattr(self.tester, 'is_pktgen') and self.tester.is_pktgen

    @property
    def pktgen_type(self):
        if self.is_pktgen_on:
            return self.tester.pktgen.pktgen_type
        else:
            return 'scapy'

    def verify_ports_number(self, port_num):
        supported_num = {
            PKTGEN_TREX: [2, 4],
            PKTGEN_IXIA: [1, 2, 4],
        }
        if not self.is_pktgen_on:
            msg = 'not using pktgen'
            self.logger.warning(msg)
            return
        # verify that enough ports are available
        _supported_num = supported_num.get(self.pktgen_type)
        msg = "Port number must be {} when using pktgen <{}>".format(
            pformat(_supported_num), self.pktgen_type)
        self.verify(len(port_num) in _supported_num, msg)
