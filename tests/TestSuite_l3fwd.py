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
Layer-3 forwarding test script.
"""

import utils
import string
import time
import re
import os
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper


class TestL3fwd(TestCase):

    path = "./examples/l3fwd/build/"
    cmdline_2_ports = {
        "1S/1C/1T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.1.0})'",
        "1S/1C/2T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.1.1})'",
        "1S/2C/1T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.2.0})'",
        "1S/4C/1T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.2.0}), (P0,1,C{1.3.0}), (P1,1,C{1.4.0})'"}

    cmdline_4_ports = {
        "1S/1C/1T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.1.0}), (P2,0,C{1.1.0}), (P3,0,C{1.1.0})'",
        "1S/2C/2T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.1.1}), (P2,0,C{1.2.0}), (P3,0,C{1.2.1})'",
        "1S/4C/1T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.2.0}), (P2,1,C{1.3.0}), (P3,1,C{1.4.0})'",
        "1S/8C/1T": "%s -c %s -n %d -- -p %s -P --config '(P0,0,C{1.1.0}), (P1,0,C{1.2.0}), (P2,0,C{1.3.0}), (P3,0,C{1,4,0}),\
        (P0,1,C{1.5.0}), (P1,1,C{1.6.0}), (P2,1,C{1.7.0}), (P3,1,C{1,8,0})'"}

    ipv4_em_table = [
        "{{IPv4(10,100,0,1), IPv4(1,2,3,4), 1, 10, IPPROTO_UDP}, P0}",
        "{{IPv4(10,101,0,1), IPv4(1,2,3,4), 1, 10, IPPROTO_UDP}, P0}",
        "{{IPv4(11,100,0,1), IPv4(1,2,3,4), 1, 11, IPPROTO_UDP}, P1}",
        "{{IPv4(11,101,0,1), IPv4(1,2,3,4), 1, 11, IPPROTO_UDP}, P1}",
        "{{IPv4(12,100,0,1), IPv4(1,2,3,4), 1, 12, IPPROTO_UDP}, P2}",
        "{{IPv4(12,101,0,1), IPv4(1,2,3,4), 1, 12, IPPROTO_UDP}, P2}",
        "{{IPv4(13,100,0,1), IPv4(1,2,3,4), 1, 13, IPPROTO_UDP}, P3}",
        "{{IPv4(13,101,0,1), IPv4(1,2,3,4), 1, 13, IPPROTO_UDP}, P3}",
    ]

    ipv4_lpm_table = [
        "{IPv4(10,100,0,0), 24, P0}",
        "{IPv4(10,101,0,0), 24, P0}",
        "{IPv4(11,100,0,0), 24, P1}",
        "{IPv4(11,101,0,0), 24, P1}",
        "{IPv4(12,100,0,0), 24, P2}",
        "{IPv4(12,101,0,0), 24, P2}",
        "{IPv4(13,100,0,0), 24, P3}",
        "{IPv4(13,101,0,0), 24, P3}",
    ]

    ipv6_em_table = [
        "{{{0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 10, IPPROTO_UDP}, P0}",
        "{{{0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 10, IPPROTO_UDP}, P0}",
        "{{{0x2a, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 11, IPPROTO_UDP}, P1}",
        "{{{0x2a, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 11, IPPROTO_UDP}, P1}",
        "{{{0x2b, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 12, IPPROTO_UDP}, P2}",
        "{{{0x2b, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 12, IPPROTO_UDP}, P2}",
        "{{{0x2c, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 13, IPPROTO_UDP}, P3}",
        "{{{0x2c, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, {0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1e, 0x67, 0xff, 0xfe, 0x0d, 0xb6, 0x0a}, 1, 13, IPPROTO_UDP}, P3}",
    ]

    ipv6_lpm_table = [
        "{{0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P0}",
        "{{0xfe, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P0}",
        "{{0x2a, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P1}",
        "{{0x2a, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P1}",
        "{{0x2b, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P2}",
        "{{0x2b, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P2}",
        "{{0x2c, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P3}",
        "{{0x2c, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x1b, 0x21, 0xff, 0xfe, 0x91, 0x38, 0x05}, 64,P3}",
    ]

    def set_up_all(self):
        """
        Run at the start of each test suite.
        L3fwd Prerequisites
        """
        self.tester.extend_external_packet_generator(TestL3fwd, self)
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]

        # Verify that enough ports are available
        self.verify(len(valports) == 2 or len(valports) == 4, "Port number must be 2 or 4.")

        # get socket and cores
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/8C/1T", socket=self.socket)
        self.verify(self.cores is not None, "Insufficient cores for speed testing")

        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]

        # Update config file and rebuild to get best perf on FVL
        if self.nic in ["fortville_sprit", "fortville_eagle", "fortville_25g"]:
            self.dut.send_expect("sed -i -e 's/CONFIG_RTE_LIBRTE_I40E_16BYTE_RX_DESC=n/CONFIG_RTE_LIBRTE_"
                                 "I40E_16BYTE_RX_DESC=y/' ./config/common_base", "#", 20)
            self.dut.build_install_dpdk(self.target)

        self.logger.info("Configure RX/TX descriptor to 2048, and re-build ./examples/l3fwd")
        self.dut.send_expect("sed -i -e 's/define RTE_TEST_RX_DESC_DEFAULT.*$/"
                             + "define RTE_TEST_RX_DESC_DEFAULT 2048/' ./examples/l3fwd/main.c", "#", 20)
        self.dut.send_expect("sed -i -e 's/define RTE_TEST_TX_DESC_DEFAULT.*$/"
                             + "define RTE_TEST_TX_DESC_DEFAULT 2048/' ./examples/l3fwd/main.c", "#", 20)
        self.method_table = {"ipv4_l3fwd_lpm": TestL3fwd.ipv4_lpm_table, "ipv4_l3fwd_em": TestL3fwd.ipv4_em_table,
                             "ipv6_l3fwd_lpm": TestL3fwd.ipv6_lpm_table, "ipv6_l3fwd_em": TestL3fwd.ipv6_em_table}

        self.pat = re.compile("P([0123])")
        self.test_results = {'header': [], 'data': []}

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def portRepl(self, match):
        """
        Function to replace P([0123]) pattern in tables
        """
        portid = match.group(1)
        self.verify(int(portid) in range(4), "invalid port id")
        if int(portid) >= len(valports):
            return '0'
        else:
            return '%s' % valports[int(portid)]

    def install_l3fwd_application(self, l3_proto, mode):
        """
        Prepare long prefix match table, replace P(x) port pattern
        """
        l3fwd_method = l3_proto + "_l3fwd_" + mode
        l3fwdStr = "static struct %s_route %s_route_array[] = {\\\n" % (l3fwd_method, l3fwd_method)
        for idx in range(len(self.method_table[l3fwd_method])):
            self.method_table[l3fwd_method][idx] = self.pat.sub(self.portRepl, self.method_table[l3fwd_method][idx])
            l3fwdStr = l3fwdStr + '' * 4 + self.method_table[l3fwd_method][idx] + ",\\\n"
        l3fwdStr = l3fwdStr + "};"
        self.dut.send_expect(r"sed -i '/%s_route_array\[\].*{/,/^\}\;/c\\%s' examples/l3fwd/l3fwd_%s.c"
                             % (l3fwd_method, l3fwdStr, mode), "# ")
        self.dut.send_expect("make clean -C examples/l3fwd", "# ")
        if "lpm" in l3fwd_method:
            out = self.dut.build_dpdk_apps("./examples/l3fwd", "USER_FLAGS=-DAPP_LOOKUP_METHOD=1")
        elif "em" in l3fwd_method:
            out = self.dut.build_dpdk_apps("./examples/l3fwd", "USER_FLAGS=-DAPP_LOOKUP_METHOD=0")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        # Backup the l3fwd exe.
        self.dut.send_expect("mv -f examples/l3fwd/build/l3fwd examples/l3fwd/build/%s" % l3fwd_method, "# ")

    def flows(self):
        """
        Return a list of packets that implements the flows described in the
        l3fwd test plan.
        """
        return {"ipv4": ['IP(src="1.2.3.4",dst="192.18.1.0")',
                         'IP(src="1.2.3.4",dst="192.18.1.1")',
                         'IP(src="1.2.3.4",dst="192.18.0.0")',
                         'IP(src="1.2.3.4",dst="192.18.0.1")',
                         'IP(src="1.2.3.4",dst="192.18.3.0")',
                         'IP(src="1.2.3.4",dst="192.18.3.1")',
                         'IP(src="1.2.3.4",dst="192.18.2.0")',
                         'IP(src="1.2.3.4",dst="192.18.2.1")'],
                "ipv6": [
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="fe80:0000:0000:0000:021b:21ff:fe91:3805")/UDP(sport=10,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="fe80:0000:0000:0000:031b:21ff:fe91:3805")/UDP(sport=10,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="2a80:0000:0000:0000:021b:21ff:fe91:3805")/UDP(sport=11,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="2a80:0000:0000:0000:031b:21ff:fe91:3805")/UDP(sport=11,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="2b80:0000:0000:0000:021b:21ff:fe91:3805")/UDP(sport=12,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="2b80:0000:0000:0000:031b:21ff:fe91:3805")/UDP(sport=12,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="2c80:0000:0000:0000:021b:21ff:fe91:3805")/UDP(sport=13,dport=1)',
                    'IPv6(src="fe80:0000:0000:0000:021e:67ff:fe0d:b60a",dst="2c80:0000:0000:0000:031b:21ff:fe91:3805")/UDP(sport=13,dport=1)'
                ]}

    def repl(self, match):
        pid = match.group(1)
        qid = match.group(2)
        self.logger.debug("%s\n" % match.group(3))
        lcid = self.dut.get_lcore_id(match.group(3))
        self.logger.debug("%s\n" % lcid)

        global corelist
        corelist.append(int(lcid))
        self.verify(int(pid) in range(4), "invalid port id")
        self.verify(lcid, "invalid thread id")
        return '%s,%s,%s' % (str(valports[int(pid)]), qid, lcid)

    def perpare_commandline(self, ports):
        """
        Generate the command line based on the number of ports
        """
        global corelist
        pat = re.compile("P([0123]),([0123]),(C\{\d.\d.\d\})")
        core_mask = {}
        if ports == 2:
            rtCmdLines = dict(TestL3fwd.cmdline_2_ports)
        elif ports == 4:
            rtCmdLines = dict(TestL3fwd.cmdline_4_ports)

        for key in rtCmdLines.keys():
            corelist = []
            while pat.search(rtCmdLines[key]):
                print rtCmdLines[key]
                rtCmdLines[key] = pat.sub(self.repl, rtCmdLines[key])
            core_mask[key] = utils.create_mask(set(corelist))
        return rtCmdLines, core_mask

    def create_pcap_file(self, frame_size, l3_proto):
        """
        Prepare traffic flow for packet generator
        """
        if l3_proto == 'ipv4':
            payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        else:
            # l3_proto == 'ipv6'
            payload_size = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ipv6'] - HEADER_SIZE['udp']
            if frame_size == 64:
                payload_size = frame_size + 2 - HEADER_SIZE['eth'] - HEADER_SIZE['ipv6'] - HEADER_SIZE['udp']

        pcaps = {}
        for _port in valports:
            index = valports[_port]
            dmac = self.dut.get_mac_address(index)
            cnt = 0
            layer3s = self.flows()[l3_proto][_port * 2:(_port + 1) * 2]
            for l3 in layer3s:
                flow = ['Ether(dst="%s")/%s/UDP()/("X"*%d)' % (dmac, l3, payload_size)]
                pcap = os.sep.join([self.output_path, "dst{0}_{1}.pcap".format(index, cnt)])
                self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, string.join(flow, ',')))
                self.tester.scapy_execute()
                if index not in pcaps:
                    pcaps[index] = []
                pcaps[index].append(pcap)
                cnt += 1
        return pcaps

    def prepare_stream(self, pcaps):
        """
        create streams for ports, one port one stream
        """
        tgen_input = []
        for rxPort in valports:
            if rxPort % len(valports) == 0 or len(valports) % rxPort == 2:
                txIntf = self.tester.get_local_port(valports[rxPort + 1])
                port_id = valports[rxPort + 1]
            else:
                txIntf = self.tester.get_local_port(valports[rxPort - 1])
                port_id = valports[rxPort - 1]
            rxIntf = self.tester.get_local_port(valports[rxPort])
            for pcap in pcaps[port_id]:
                tgen_input.append((txIntf, rxIntf, pcap))
        return tgen_input

    def create_result_table(self, ttl, ttl1, ttl2, ttl3, ttl4):

        header_row = [ttl, ttl1, ttl2, ttl3, ttl4]
        self.test_results['header'] = header_row
        self.result_table_create(header_row)
        self.test_results['data'] = []

    def measure_throughput(self, l3_proto, mode):
        """
        measure throughput according to Layer-3 Protocal and Lookup Mode
        """
        # create result table
        self.create_result_table("Frame Size", "Mode", "S/C/T", "Mpps", "% Linerate")
        # build application
        self.install_l3fwd_application(l3_proto, mode)
        # perpare commandline and core mask
        rtCmdLines, core_mask = self.perpare_commandline(len(valports))

        for cores in rtCmdLines.keys():
            # Start L3fwd appliction
            command_line = rtCmdLines[cores] % (TestL3fwd.path + l3_proto + "_l3fwd_" + mode, core_mask[cores],
                                                self.dut.get_memory_channels(), utils.create_mask(valports))
            self.dut.send_expect(command_line, "L3FWD:", 120)
            for frame_size in self.frame_sizes:
                # crete traffic flow
                pcaps = self.create_pcap_file(frame_size, l3_proto)
                # send the traffic and Measure test
                tgenInput = self.prepare_stream(pcaps)

                vm_config = self.set_fields()
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, vm_config, self.tester.pktgen)
                # set traffic option
                traffic_opt = {'delay': 30}
                _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
                self.verify(pps > 0, "No traffic detected")
                # statistical result
                pps /= 1000000.0
                linerate = self.wirespeed(self.nic, frame_size, len(valports))
                percentage = pps * 100 / linerate
                if mode == "ipv6" and frame_size == 64:
                    frame_size += 2
                data_row = [frame_size, mode, cores, str(pps), str(percentage)]
                self.result_table_add(data_row)
                self.test_results['data'].append(data_row)
            # Stop L3fwd
            self.dut.send_expect("^C", "#")
            time.sleep(1)
        # Print result
        self.result_table_print()

    def measure_rfc2544(self, l3_proto, mode):
        """
        measure RFC2544 according to Layer-3 Protocal and Lookup Mode
        """
        # create result table
        self.create_result_table("Frame Size", "Mode", "S/C/T", "Zero Loss Throughput(Mpps)", " % Zero Loss Rate")
        # build application
        self.install_l3fwd_application(l3_proto, mode)
        # perpare commandline and core mask
        rtCmdLines, core_mask = self.perpare_commandline(len(valports))

        for frame_size in self.frame_sizes:
            for cores in rtCmdLines.keys():
                # in order to save time, only some of the cases will be run.
                if cores in ["1S/2C/1T", "1S/4C/1T"]:
                    # Start L3fwd appliction
                    command_line = rtCmdLines[cores] % (TestL3fwd.path + l3_proto + "_l3fwd_" + mode, core_mask[cores],
                                                        self.dut.get_memory_channels(), utils.create_mask(valports))
                    if self.nic == "niantic":
                        command_line += " --parse-ptype"
                    if frame_size > 1518:
                        command_line += " --enable-jumbo --max-pkt-len %d" % frame_size
                    self.dut.send_expect(command_line, "L3FWD:", 120)
                    self.logger.info("Executing l3fwd using %s mode, %d ports, %s and %d frame size"
                                     % (mode, len(valports), cores, frame_size))
                    # crete traffic flow
                    pcaps = self.create_pcap_file(frame_size, l3_proto)
                    # send the traffic and Measure test
                    tgenInput = self.prepare_stream(pcaps)

                    vm_config = self.set_fields()
                    # clear streams before add new streams
                    self.tester.pktgen.clear_streams()
                    # run packet generator
                    streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, vm_config, self.tester.pktgen)
                    # set traffic option
                    traffic_opt = {'duration': 15}
                    zero_loss_rate, tx_pkts, rx_pkts = self.tester.pktgen.measure_rfc2544(stream_ids=streams,
                                                                                          options=traffic_opt)
                    # statistical result
                    linerate = self.wirespeed(self.nic, frame_size, len(valports))
                    zero_loss_throughput = (linerate * zero_loss_rate) / 100
                    if mode == "ipv6" and frame_size == 64:
                        frame_size += 2
                    data_row = [frame_size, mode, cores, str(zero_loss_throughput), str(zero_loss_rate)]
                    self.result_table_add(data_row)
                    self.test_results['data'].append(data_row)
                # Stop L3fwd
                self.dut.send_expect("^C", "#")
                time.sleep(1)
        # Print result
        self.result_table_print()

    def test_perf_rfc2544_ipv4_lpm(self):
        self.measure_rfc2544(l3_proto="ipv4", mode="lpm")

    def test_perf_rfc2544_ipv4_em(self):
        self.measure_rfc2544(l3_proto="ipv4", mode="em")

    def test_perf_throughput_ipv4_lpm(self):
        self.measure_throughput(l3_proto="ipv4", mode="lpm")

    def test_perf_throughput_ipv4_em(self):
        self.measure_throughput(l3_proto="ipv4", mode="em")

    def test_perf_rfc2544_ipv6_lpm(self):
        self.measure_rfc2544(l3_proto="ipv6", mode="lpm")

    def test_perf_rfc2544_ipv6_em(self):
        self.measure_rfc2544(l3_proto="ipv6", mode="em")

    def test_perf_throughput_ipv6_lpm(self):
        self.measure_throughput(l3_proto="ipv6", mode="lpm")

    def test_perf_throughput_ipv6_em(self):
        self.measure_throughput(l3_proto="ipv6", mode="em")

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {'ip':  {'src': {'action': 'random'}, }, }
        return fields_config

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
