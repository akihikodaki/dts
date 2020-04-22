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
import re
from collections import Counter
from datetime import datetime

from packet import Packet
from scapy.sendrecv import sendp

from utils import create_mask as dts_create_mask
from test_case import TestCase
from exception import VerifyFailure
from settings import HEADER_SIZE
from functools import reduce


class TestFlowClassify(TestCase):

    def is_existed_on_crb(self, check_path, crb='dut'):
        alt_session = self.dut.alt_session \
                      if crb == 'dut' else \
                      self.tester.alt_session
        alt_session.send_expect("ls %s > /dev/null 2>&1" % check_path, "# ")
        cmd = "echo $?"
        output = alt_session.send_expect(cmd, "# ")
        ret = True if output and output.strip() == "0" else False
        return ret

    def get_cores_mask(self, config='all'):
        sockets = [self.dut.get_numa_id(index) for index in self.dut_ports]
        socket_count = Counter(sockets)
        port_socket = list(socket_count.keys())[0] if len(socket_count) == 1 else -1
        mask = dts_create_mask(self.dut.get_core_list(config,
                                                      socket=port_socket))
        return mask

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

    def get_ixia_peer_port(self):
        for cnt in self.dut_ports:
            if self.tester.get_local_port_type(cnt) != 'ixia':
                continue
            tester_port = self.tester.get_local_port(cnt)
            return tester_port

    def d_console(self, cmds):
        return self.execute_cmds(cmds, con_name='dut')

    def d_a_console(self, cmds):
        return self.execute_cmds(cmds, con_name='dut_alt')

    def get_console(self, name):
        if name == 'dut':
            console = self.dut.send_expect
            msg_pipe = self.dut.get_session_output
        elif name == 'dut_alt':
            console = self.dut.alt_session.send_expect
            msg_pipe = self.dut.alt_session.session.get_output_all
        else:
            msg = 'not support <{}> session'.format(name)
            raise VerifyFailure(msg)
        return console, msg_pipe

    def execute_cmds(self, cmds, con_name):
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
                # self.check_process_status()
                msg = "execute '{0}' timeout".format(item[0])
                raise Exception(msg)
            time.sleep(1)
            if len(cmds) > 1:
                outputs.append(output)
            else:
                outputs = output
        return outputs

    def get_pkt_len(self, pkt_type):
        # packet size
        frame_size = 256
        headers_size = sum(
            [132 if x == 'sctp' else HEADER_SIZE[x] for x in ['eth', 'ip', pkt_type]])
        pktlen = frame_size - headers_size
        return pktlen

    def set_stream(self, stm_names=None):
        ''' set streams for traffic '''
        pkt_configs = {
            # UDP_1:
            #    Frame Data/Protocols: Ethernet 2 0800, IPv4,UDP/IP, Fixed 64.
            #    IPv4 Header Page: Dest Address: 2.2.2.7 Src  Address: 2.2.2.3
            #    UDP Header: Src Port: 32  Dest Port: 33
            #
            #    Stream Control: Stop after this Stream, Packet Count 32.
            #
            'UDP_1': {
                'type': 'UDP',
                'pkt_layers': {
                    'ipv4': {'src': '2.2.2.3', 'dst': '2.2.2.7'},
                    'udp': {'src': 32, 'dst': 33},
                    'raw': {'payload': ['58'] * self.get_pkt_len('udp')}}},
            # UDP_2:
            #    Frame Data/Protocols: Ethernet 2 0800, IPv4,UDP/IP, Fixed 64.
            #    IPv4 Header Page: Dest Address: 9.9.9.7 Src  Address: 9.9.9.3
            #    UDP Header: Src Port: 32  Dest Port: 33
            #
            #    Stream Control: Stop after this Stream, Packet Count 32.
            #
            'UDP_2': {
                'type': 'UDP',
                'pkt_layers': {
                    'ipv4': {'src': '9.9.9.3', 'dst': '9.9.9.7'},
                    'udp': {'src': 32, 'dst': 33},
                    'raw': {'payload': ['58'] * self.get_pkt_len('udp')}}},
            'invalid_UDP': {
                'type': 'UDP',
                'pkt_layers': {
                    'ipv4': {'src': '9.8.7.6', 'dst': '192.168.0.36'},
                    'udp': {'src': 10, 'dst': 11},
                    'raw': {'payload': ['58'] * self.get_pkt_len('udp')}}},
            # TCP_1:
            #    Frame Data/Protocols: Ethernet 2 0800, IPv4,TCP/IP, Fixed 64.
            #    IPv4 Header Page: Dest Address: 9.9.9.7 Src  Address: 9.9.9.3
            #    TCP Header: Src Port: 32  Dest Port: 33
            #
            #    Stream Control: Stop after this Stream, Packet Count 32.
            #
            'TCP_1': {
                'type': 'TCP',
                'pkt_layers': {
                    'ipv4': {'src': '9.9.9.3', 'dst': '9.9.9.7'},
                    'tcp': {'src': 32, 'dst': 33},
                    'raw': {'payload': ['58'] * self.get_pkt_len('tcp')}}},
            # TCP_2:
            #    Frame Data/Protocols: Ethernet 2 0800, IPv4,TCP/IP, Fixed 64.
            #    IPv4 Header Page: Dest Address: 9.9.8.7 Src  Address: 9.9.8.3
            #    TCP Header: Src Port: 32  Dest Port: 33
            #
            #    Stream Control: Stop after this Stream, Packet Count 32.
            #
            'TCP_2': {
                'type': 'TCP',
                'pkt_layers': {
                    'ipv4': {'src': '9.9.8.3', 'dst': '9.9.8.7'},
                    'tcp': {'src': 32, 'dst': 33},
                    'raw': {'payload': ['58'] * self.get_pkt_len('tcp')}}},
            'invalid_TCP': {
                'type': 'TCP',
                'pkt_layers': {
                    'ipv4': {'src': '9.8.7.6', 'dst': '192.168.0.36'},
                    'tcp': {'src': 10, 'dst': 11},
                    'raw': {'payload': ['58'] * self.get_pkt_len('tcp')}}},
            # SCTP_1:
            #    Frame Data/Protocols: Ethernet 2 0800, IPv4, None, Fixed 256.
            #    IPv4 Header Page: Dest Address: 2.3.4.5 Src  Address: 6.7.8.9
            #    Protocol: 132-SCTP
            #    Stream Control: Stop after this Stream, Packet Count 32.
            #
            'SCTP_1': {
                'type': 'SCTP',
                'pkt_layers': {
                    'ipv4': {'src': '6.7.8.9', 'dst': '2.3.4.5'},
                    'sctp': {'src': 32, 'dst': 33},
                    'raw': {'payload': ['58'] * self.get_pkt_len('sctp')}}},
            'invalid_SCTP': {
                'type': 'SCTP',
                'pkt_layers': {
                    'ipv4': {'src': '9.8.7.6', 'dst': '192.168.0.36'},
                    'sctp': {'src': 10, 'dst': 11},
                    'raw': {'payload': ['58'] * self.get_pkt_len('sctp')}}},
        }

        # create packet for send
        streams = []
        for stm_name in stm_names:
            if stm_name not in list(pkt_configs.keys()):
                continue
            values = pkt_configs[stm_name]
            savePath = os.sep.join([self.output_path,
                                    "pkt_{0}.pcap".format(stm_name)])
            pkt_type = values.get('type')
            pkt_layers = values.get('pkt_layers')
            pkt = Packet(pkt_type=pkt_type)
            for layer in list(pkt_layers.keys()):
                pkt.config_layer(layer, pkt_layers[layer])
            pkt.pktgen.pkt.show()
            streams.append(pkt.pktgen.pkt)
        return streams

    def send_packet_by_scapy(self, config):
        tx_iface = config.get('tx_intf')
        cmd = "ifconfig {0} up".format(tx_iface)
        self.tester.send_expect(cmd, '# ', 30)
        pkts = config.get('stream')
        # stream config
        stream_configs = config.get('stream configs')
        frame_config = stream_configs.get('frame config')
        gapUnit = frame_config.get('gapUnit')
        if gapUnit == 'gapMilliSeconds':
            time_unit = 10e-4
        elif gapUnit == 'gapMicroSeconds':
            time_unit = 10e-7
        else:
            time_unit = 1
        time_unit = 10e-4
        ifg = frame_config.get('ifg')
        count = stream_configs.get('count')
        interval = ifg * time_unit
        # run traffic
        sendp(pkts, iface=tx_iface, inter=interval, verbose=False, count=count)

    @property
    def target_dir(self):
        ''' get absolute directory of target source code '''
        target_dir = '/root' + self.dut.base_dir[1:] \
                     if self.dut.base_dir.startswith('~') else \
                     self.dut.base_dir
        return target_dir

    @property
    def target_name(self):
        return self.dut.target

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

    def start_flow_classify(self):
        ''' boot up flow_classify '''
        rule_config = os.sep.join([self.target_dir,
                                   'examples',
                                   'flow_classify',
                                   'ipv4_rules_file.txt'])
        if not self.is_existed_on_crb(rule_config):
            raise VerifyFailure("rules file doesn't existed")
        core = "1S/1C/1T"
        eal_params = self.dut.create_eal_parameters()
        #option = r" -c {0} - n 4  --file-prefix=test {1} -- --rule_ipv4={2}".format(self.get_cores_mask(core),eal_params,rule_config)
        option = r" {0} -- --rule_ipv4={1}".format(eal_params,rule_config)
        prompt = 'table_entry_delete succeeded'
        cmd = [' '.join([self.flow_classify, option]), prompt, 30]
        output = self.d_console(cmd)
        return output

    def close_flow_classify(self):
        output = self.dut.get_session_output()
        dt = datetime.now()
        timestamp = dt.strftime('%Y-%m-%d_%H%M%S')
        self.test_data = '{0}/{1}_{2}.log'.format(
            self.output_path, 'flow_classify', timestamp)
        with open(self.test_data, 'w') as fp:
            fp.write(output)
        cmds = ['killall flow_classify', '# ', 10]
        self.d_a_console(cmds)

    def get_stream_rule_priority(self, stream_type):
        stream_types = {
            'UDP_1': 0,
            'UDP_2': 1,
            'TCP_1': 2,
            'TCP_2': 3,
            'SCTP_1': 4}
        return stream_types.get(stream_type, None)

    def run_traffic(self, config):
        stm_types = config.get('stm_types')
        total_packets = config.get('total_packets')
        gap = config.get('gap')
        flow_type = config.get('flow_type')
        # set traffic topology
        pktgen_name = 'ixia' if self._enable_perf else 'scapy'
        tx_port = self.get_ixia_peer_port() if pktgen_name == 'ixia' else \
            self.tester.get_interface(self.tester.get_local_port(0))
        # set traffic configuration
        ports_topo = {
            'tx_intf': tx_port,
            'rx_intf': 0,
            'stream': self.set_stream(stm_types),
            'stream configs': {
                'count': total_packets,
                'frame config': {
                    'gapUnit': 'gapMilliSeconds',
                    'ifg': gap},
                'flow_type': flow_type,
            }, }
        # begin traffic checking
        self.logger.info("begin traffic ... ")
        method_name = 'send_packet_by_' + pktgen_name
        print('pktname is %s'% pktgen_name)
        pkt_gen_func = getattr(self, 'send_packet_by_' + pktgen_name)
        if pkt_gen_func:
            result = pkt_gen_func(ports_topo)
        else:
            msg = 'not support {}'.format(method_name)
            raise VerifyFailure(msg)
        # end traffic
        self.logger.info("complete transmission")

    def check_filter_pkts(self, log, rule_priority):
        pat = "rule\[{0}\] count=(\d+)".format(rule_priority) \
              if rule_priority is not None else \
              "rule\[\d+\] count=(\d+)"
        with open(log, 'r') as fp:
            content = fp.read()
        if content:
            grp = re.findall(pat, content, re.M)
            total = reduce(lambda x, y: x + y, [int(i) for i in grp]) \
                if grp and len(grp) else 0
        return total

    def check_test_result(self, config):
        stm_types = config.get('stm_types')
        total_packets = config.get('total_packets')
        flow_type = config.get('flow_type')
        self.logger.info(stm_types)
        check_results = []
        for stm_type in stm_types:
            rule_priority = self.get_stream_rule_priority(stm_type)
            captured_pkts = self.check_filter_pkts(self.test_data,
                                                   rule_priority)
            self.logger.info("%s %d %d" % (stm_type, rule_priority or 0,
                                           captured_pkts or 0))
            msg = None
            if flow_type == 'multi_stream':
                # check if packets are multiple rules' pkts
                # ignore invalid rule
                if rule_priority and captured_pkts % total_packets != 0:
                    msg = ("captured packets are not multiples of "
                           "rules' {0} packets".format(total_packets))
                else:
                    continue
            elif flow_type == 'single_stream':
                if rule_priority is None and captured_pkts != 0:
                    msg = "invalid stream hasn't been filtered out"
                elif rule_priority and captured_pkts != total_packets:
                    msg = "expect {0} ".format(total_packets) + \
                          "captured {0}".format(captured_pkts)
                else:
                    continue
            else:
                continue
            if msg:
                check_results.append(msg)

        if check_results:
            self.logger.error(os.linesep.join(check_results))
            raise VerifyFailure("test result fail")

    def init_params(self):
        self.test_data = None

    def verify_traffic(self, stm_types=None, gap=10,
                       flow_type="single_stream"):
        self.logger.info('begin to check ...... ')
        info = {
            'stm_types': stm_types,
            'flow_type': flow_type,
            'total_packets': 32,
            'gap': gap, }

        try:
            self.init_params()
            # preset test environment
            self.start_flow_classify()
            # run traffic
            self.run_traffic(info)
            # close flow_classify
            self.close_flow_classify()
        except Exception as e:
            print(e)
            # close flow_classify
            self.close_flow_classify()
            msg = 'failed to run traffic'
            self.verify(False, msg)
        # analysis test result
        self.check_test_result(info)

    def verify_multiple_rules(self):
        stream_list = [
            'UDP_1', 'UDP_2', 'invalid_UDP',
            'TCP_1', 'TCP_2', 'invalid_TCP',
            'SCTP_1', 'invalid_SCTP']
        self.verify_traffic(stm_types=stream_list, flow_type="multi_stream")

    def verify_supported_nic(self):
        supported_drivers = ['i40e', 'ixgbe', 'igc', 'igb']
        result = all([self.dut.ports_info[index]['port'].default_driver in
                      supported_drivers
                      for index in self.dut_ports])
        msg = "current nic is not supported"
        self.verify(result, msg)
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run before each test suite
        """
        # initialize ports topology
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        # set binary process setting
        self.flow_classify = self.prepare_binary('flow_classify')
        self.verify_supported_nic()

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

    def test_udp_valid_rule(self):
        stream_list = ['UDP_1', 'UDP_2']
        for stm_type in stream_list:
            self.verify_traffic([stm_type])

    def test_udp_invalid_rule(self):
        stream_list = ['invalid_UDP']
        self.verify_traffic(stream_list)

    def test_tcp_valid_rule(self):
        stream_list = ['TCP_1', 'TCP_2']
        for stm_type in stream_list:
            self.verify_traffic([stm_type])

    def test_tcp_invalid_rule(self):
        stream_list = ['invalid_TCP']
        self.verify_traffic(stream_list)

    def test_sctp_valid_rule(self):
        stream_list = ['SCTP_1']
        self.verify_traffic(stream_list)

    def test_sctp_invalid_rule(self):
        stream_list = ['invalid_SCTP']
        self.verify_traffic(stream_list)

    def test_multiple_rules(self):
        self.verify_multiple_rules()
