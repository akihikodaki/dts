# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

import utils
import re
import time
import socket

from settings import HEADER_SIZE
from test_case import TestCase
from pmd_output import PmdOutput
from settings import DRIVERS
from crb import Crb

from virt_dut import VirtDut
from project_dpdk import DPDKdut
from dut import Dut
from packet import Packet

import os
import random
from exception import VerifyFailure
import scapy.layers.inet
from scapy.utils import rdpcap

from time import sleep
# from scapy.all import conf
from scapy.utils import wrpcap, rdpcap, hexstr
from scapy.layers.inet import Ether, IP, TCP, UDP, ICMP
from scapy.layers.l2 import Dot1Q, ARP, GRE
from scapy.layers.sctp import SCTP, SCTPChunkData
from scapy.route import *
from scapy.packet import bind_layers, Raw
from scapy.arch import get_if_hwaddr
from scapy.sendrecv import sniff
from scapy.sendrecv import sendp

import itertools

MODE = 1  # 0: Development, 1: Release

TIMESTAMP = re.compile(r'\d{2}\:\d{2}\:\d{2}\.\d{6}')
PAYLOAD = re.compile(r'\t0x([0-9a-fA-F]+):  ([0-9a-fA-F ]+)')

FILE_DIR = os.path.dirname(os.path.abspath(__file__)).split(os.path.sep)
DEP_DIR = os.path.sep.join(FILE_DIR[:-1]) + '/dep/'

BUFFER_SIZE = 1024
CLI_SERVER_CONNECT_DELAY = 1


class TestPipeline(TestCase):

    def pair_hex_digits(self, iterable, count, fillvalue=None):
        args = [iter(iterable)] * count
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    def convert_tcpdump_to_text2pcap(self, in_filename, out_filename):
        with open(in_filename) as input, open(out_filename, 'w') as output:
            output.write('# SPDX-License-Identifier: BSD-3-Clause\n')
            output.write('# Copyright(c) 2020 Intel Corporation\n')
            output.write('#\n\n')
            output.write('# text to pcap: text2pcap packet.txt packet.pcap\n')
            output.write('# pcap to text: tcpdump -r packet.pcap -xx\n\n')

            i = 0
            flag_line_completed = 0
            for line in input:
                time = TIMESTAMP.match(line)
                if time:
                    # print("time match")
                    if flag_line_completed == 1:
                        flag_line_completed = 0
                        output.write('\n# Packet {}\n'.format(i))
                    else:
                        output.write('# Packet {}\n'.format(i))
                    i += 1
                    continue
                payload = PAYLOAD.match(line)
                if payload:
                    # print("payload match")
                    address = payload.group(1)
                    hex_data = payload.group(2).replace(' ', '')
                    hex_data = ' '.join(''.join(part) for part in self.pair_hex_digits(hex_data, 2, ' '))
                    # print('{}  {}'.format(address, hex_data))
                    # print(len(hex_data))
                    if (len(hex_data) < 47):
                        output.write('{:0>6}  {:<47}\n'.format(address, hex_data))
                        output.write('\n')
                        flag_line_completed = 0
                    else:
                        output.write('{:0>6}  {:<47}\n'.format(address, hex_data))
                        flag_line_completed = 1

            if flag_line_completed == 1:
                output.write('\n')

    def get_flow_direction_param_of_tcpdump(self):
        """
        get flow dirction param depend on tcpdump version
        """
        param = ""
        direct_param = r"(\s+)\[ (\S+) in\|out\|inout \]"
        out = self.tester.send_expect('tcpdump -h', '# ')
        for line in out.split('\n'):
            m = re.match(direct_param, line)
            if m:
                opt = re.search("-Q", m.group(2))
                if opt:
                    param = "-Q" + " in"
                else:
                    opt = re.search("-P", m.group(2))
                    if opt:
                        param = "-P" + " in"
        if len(param) == 0:
            self.logger.info("tcpdump not support direction choice!!!")
        return param

    def tcpdump_start_sniff(self, interface, filters=""):
        """
        Starts tcpdump in the background to sniff packets that received by interface.
        """
        command = 'rm -f /tmp/tcpdump_{0}.pcap'.format(interface)
        self.tester.send_expect(command, '#')
        command = 'tcpdump -nn -e {0} -w /tmp/tcpdump_{1}.pcap -i {1} {2} 2>/tmp/tcpdump_{1}.out &'\
                  .format(self.param_flow_dir, interface, filters)
        self.tester.send_expect(command, '# ')

    def tcpdump_stop_sniff(self):
        """
        Stops the tcpdump process running in the background.
        """
        self.tester.send_expect('killall tcpdump', '# ')
        # For the [pid]+ Done tcpdump... message after killing the process
        sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', '# ')
        sleep(1)

    def write_pcap_file(self, pcap_file, pkts):
        try:
            wrpcap(pcap_file, pkts)
        except:
            raise Exception("write pcap error")

    def read_pcap_file(self, pcap_file):
        pcap_pkts = []
        try:
            pcap_pkts = rdpcap(pcap_file)
        except:
            raise Exception("write pcap error")

        return pcap_pkts

    def send_and_sniff_pkts(self, from_port, to_port, in_pcap_file, out_pcap_file, filters=""):
        """
        Sent pkts that read from the pcap_file.
        Return the sniff pkts.
        """
        tx_port = self.tester.get_local_port(self.dut_ports[from_port])
        rx_port = self.tester.get_local_port(self.dut_ports[to_port])

        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)

        self.tester.send_expect('rm -f /tmp/*.txt /tmp/*.pcap /tmp/*.out', '# ')
        self.tcpdump_start_sniff(rx_interface, filters)

        # Prepare the pkts to be sent
        self.tester.scapy_foreground()
        self.tester.send_expect('text2pcap -q {} /tmp/packet_tx.pcap'.format('/tmp/' + in_pcap_file), '# ')
        self.tester.scapy_append('pkt = rdpcap("/tmp/packet_tx.pcap")')
        self.tester.scapy_append('sendp(pkt, iface="{}", count=1)'.format(tx_interface))
        self.tester.scapy_execute()
        self.tcpdump_stop_sniff()
        self.tester.send_expect(
            'tcpdump -n -r /tmp/tcpdump_{}.pcap -xx > /tmp/packet_rx.txt'.format(rx_interface), '# ')
        self.convert_tcpdump_to_text2pcap('/tmp/packet_rx.txt', '/tmp/packet_rx_rcv.txt')
        out = self.tester.send_command(
            'diff -sqw /tmp/packet_rx_rcv.txt {}'.format('/tmp/' + out_pcap_file), timeout=0.5)
        if "are identical" not in out:
            self.dut.send_expect('^C', '# ')
            self.verify(False, "Output pcap files mismatch error")

    def send_and_sniff_multiple(self, from_port, to_port, in_pcap, out_pcap, filters, rate=0):

        self.tester.send_expect('rm -f /tmp/*.txt /tmp/*.pcap /tmp/*.out', '# ')
        tx_count = len(from_port)
        rx_count = len(to_port)
        tx_port, rx_port, tx_inf, rx_inf = ([] for i in range(4))

        for i in range(tx_count):
            tx_port.append(self.tester.get_local_port(self.dut_ports[from_port[i]]))
            tx_inf.append(self.tester.get_interface(tx_port[i]))

        for i in range(rx_count):
            rx_port.append(self.tester.get_local_port(self.dut_ports[to_port[i]]))
            rx_inf.append(self.tester.get_interface(rx_port[i]))
            self.tcpdump_start_sniff(rx_inf[i], filters[i])

        self.tester.scapy_foreground()
        for i in range(tx_count):
            self.tester.send_expect(
                'text2pcap -q {} /tmp/tx_{}.pcap'.format('/tmp/' + in_pcap[i], tx_inf[i]), '# ')
            self.tester.scapy_append('pkt = rdpcap("/tmp/tx_{}.pcap")'.format(tx_inf[i]))
            if rate:
                self.tester.scapy_append(
                    'sendp(pkt, iface="{}", count=1, inter=1./{})'.format(tx_inf[i], rate))
            else:
                self.tester.scapy_append('sendp(pkt, iface="{}", count=1)'.format(tx_inf[i]))

        self.tester.scapy_execute()
        self.tcpdump_stop_sniff()
        mismatch_count = 0
        for i in range(rx_count):
            self.tester.send_expect(
                'tcpdump -n -r /tmp/tcpdump_{}.pcap -xx > /tmp/packet_rx.txt'.format(rx_inf[i]), '# ')
            self.convert_tcpdump_to_text2pcap(
                '/tmp/packet_rx.txt', '/tmp/packet_rx_rcv_{}.txt'.format(rx_inf[i]))
            cmd = 'diff -sqw /tmp/packet_rx_rcv_{}.txt {}'.format(rx_inf[i], '/tmp/' + out_pcap[i])
            out = self.tester.send_command(cmd, timeout=0.5)
            if "are identical" not in out:
                mismatch_count += 1
        if mismatch_count:
            self.dut.send_expect('^C', '# ')
            self.verify(False, "Output pcap files mismatch error")

    def setup_env(self, port_nums, driver):
        """
        This is to set up vf environment.
        The pf is bound to dpdk driver.
        """
        self.dut.send_expect("modprobe vfio-pci", "# ")
        if driver == 'default':
            for port_id in self.dut_ports:
                port = self.dut.ports_info[port_id]['port']
                port.bind_driver()
        # one PF generate one VF
        for port_num in range(port_nums):
            self.dut.generate_sriov_vfs_by_port(self.dut_ports[port_num], 1, driver)
            self.sriov_vfs_port.append(self.dut.ports_info[self.dut_ports[port_num]]['vfs_port'])
        if driver == 'default':
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf0_interface, self.vf0_mac), "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf1_interface, self.vf1_mac), "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf2_interface, self.vf2_mac), "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf3_interface, self.vf3_mac), "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" % self.pf0_interface, "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" % self.pf1_interface, "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" % self.pf2_interface, "# ", 3)
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" % self.pf3_interface, "# ", 3)

        try:
            for port_num in range(port_nums):
                for port in self.sriov_vfs_port[port_num]:
                    port.bind_driver(driver="vfio-pci")
        except Exception as e:
            self.destroy_env(port_nums, driver)
            raise Exception(e)

    def destroy_env(self, port_nums, driver):
        """
        This is to stop testpmd and destroy vf environment.
        """
        cmd = "^C"
        self.session_secondary.send_expect(cmd, "# ", 20)
        time.sleep(5)
        if driver == self.drivername:
            self.dut.send_expect("quit", "# ")
            time.sleep(5)
        for port_num in range(port_nums):
            self.dut.destroy_sriov_vfs_by_port(self.dut_ports[port_num])

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.port_nums = 4
        self.verify(len(self.dut_ports) >= self.port_nums,
                    "Insufficient ports for speed testing")

        self.dut_p0_pci = self.dut.get_port_pci(self.dut_ports[0])
        self.dut_p1_pci = self.dut.get_port_pci(self.dut_ports[1])
        self.dut_p2_pci = self.dut.get_port_pci(self.dut_ports[2])
        self.dut_p3_pci = self.dut.get_port_pci(self.dut_ports[3])

        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.dut_p1_mac = self.dut.get_mac_address(self.dut_ports[1])
        self.dut_p2_mac = self.dut.get_mac_address(self.dut_ports[2])
        self.dut_p3_mac = self.dut.get_mac_address(self.dut_ports[3])

        self.pf0_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf1_interface = self.dut.ports_info[self.dut_ports[1]]['intf']
        self.pf2_interface = self.dut.ports_info[self.dut_ports[2]]['intf']
        self.pf3_interface = self.dut.ports_info[self.dut_ports[3]]['intf']

        self.vf0_mac = "00:11:22:33:44:55"
        self.vf1_mac = "00:11:22:33:44:56"
        self.vf2_mac = "00:11:22:33:44:57"
        self.vf3_mac = "00:11:22:33:44:58"

        ports = [self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci]
        self.eal_para = self.dut.create_eal_parameters(cores=list(range(4)), ports=ports)
        self.sriov_vfs_port = []
        self.session_secondary = self.dut.new_session()

        out = self.dut.build_dpdk_apps("./examples/pipeline")
        self.verify("Error" not in out, "Compilation error")
        self.app_pipeline_path = self.dut.apps_name['pipeline']
        self.app_testpmd_path = self.dut.apps_name['test-pmd']
        self.param_flow_dir = self.get_flow_direction_param_of_tcpdump()

        # update the ./dep/pipeline.tar.gz file
        PIPELINE_TAR_FILE = DEP_DIR + 'pipeline.tar.gz'
        self.tester.send_expect('rm -rf /tmp/pipeline', '# ')
        if MODE == 0:  # Development
            self.tester.send_expect('rm -rf {}'.format(PIPELINE_TAR_FILE), '# ')
            self.tester.send_expect('tar -czf {} -C {} pipeline/'.format(PIPELINE_TAR_FILE, DEP_DIR), '# ')
        self.tester.send_expect('tar -zxf {} --directory /tmp'.format(PIPELINE_TAR_FILE), "# ", 20)

        # copy the ./dep/pipeline.tar.gz file to DUT
        self.dut.send_expect('rm -rf /tmp/pipeline.tar.gz /tmp/pipeline', "# ", 20)
        self.session_secondary.copy_file_to('dep/pipeline.tar.gz', '/tmp/')
        self.dut.send_expect('tar -zxf /tmp/pipeline.tar.gz --directory /tmp', "# ", 20)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def connect_cli_server(self):

        SERVER_IP = '192.168.122.216'
        SERVER_PORT = 8086

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((SERVER_IP, SERVER_PORT))
                sleep(1)
                msg = s.recv(BUFFER_SIZE)
                response = msg.decode()
                # print('Rxd: ' + response)
                if "pipeline>" not in response:
                    s.close()
                    self.verify(0, "CLI Response Error")
                else:
                    return s
            except socket.error as err:
                print("Socket connection failed with error %s" % (err))
                self.verify(0, "Failed to connect to server")
        except socket.error as err:
            print("Socket creation failed with error %s" % (err))
            self.verify(0, "Failed to create socket")

    def socket_send_cmd(self, socket, cmd, expected_rsp):

        socket.send(cmd.encode('utf-8'))
        sleep(0.1)
        msg = socket.recv(BUFFER_SIZE)
        response = msg.decode()
        print('Rxd: ' + response)
        if expected_rsp not in response:
            socket.close()
            self.dut.send_expect("^C", "# ", 20)
            self.verify(0, "CLI Response Error")

    def run_dpdk_app(self, cli_file):

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "{0} {1} -- -s {2}".format(self.app_pipeline_path, self.eal_para, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 75)

    def send_pkts(self, from_port, to_port, in_pcap_file):
        """
        Send pkts read from the input pcap file.
        """
        tx_port = self.tester.get_local_port(self.dut_ports[from_port])
        rx_port = self.tester.get_local_port(self.dut_ports[to_port])

        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)

        self.tester.send_expect('rm -f /tmp/*.txt /tmp/*.pcap /tmp/*.out', '# ')

        # Prepare the pkts to be sent
        self.tester.scapy_foreground()
        self.tester.send_expect('text2pcap -q {} /tmp/packet_tx.pcap'.format('/tmp/' + in_pcap_file), '# ')
        self.tester.scapy_append('pkt = rdpcap("/tmp/packet_tx.pcap")')
        self.tester.scapy_append('sendp(pkt, iface="{}", count=1)'.format(tx_interface))
        self.tester.scapy_execute()

    def test_rx_tx_001(self):

        cli_file = '/tmp/pipeline/rx_tx_001/rx_tx_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/rx_tx_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/rx_tx_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_001(self):

        cli_file = '/tmp/pipeline/extract_emit_001/extract_emit_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_002(self):

        cli_file = '/tmp/pipeline/extract_emit_002/extract_emit_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_003(self):

        cli_file = '/tmp/pipeline/extract_emit_003/extract_emit_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_004(self):

        cli_file = '/tmp/pipeline/extract_emit_004/extract_emit_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_005(self):

        cli_file = '/tmp/pipeline/extract_emit_005/extract_emit_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_005/pcap_files/out_1.txt'] * 4
        filters = ["vlan"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_006(self):

        cli_file = '/tmp/pipeline/extract_emit_006/extract_emit_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_006/pcap_files/out_1.txt'] * 4
        filters = ["udp port 4789"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_007(self):

        cli_file = '/tmp/pipeline/extract_emit_007/extract_emit_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_007/pcap_files/out_1.txt'] * 4
        filters = ["udp port 4789"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_008(self):

        cli_file = '/tmp/pipeline/extract_emit_008/extract_emit_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_008/pcap_files/out_1.txt'] * 4
        filters = ["udp port 4789"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_extract_emit_009(self):

        cli_file = '/tmp/pipeline/extract_emit_009/extract_emit_009.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/extract_emit_009/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/extract_emit_009/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_001(self):

        cli_file = '/tmp/pipeline/and_001/and_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_002(self):

        cli_file = '/tmp/pipeline/and_002/and_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = 'pipeline/and_002/pcap_files/in_1.txt'
        out_pcap = 'pipeline/and_002/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(1, 0, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(2, 0, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(3, 0, in_pcap, out_pcap, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_and_003(self):

        cli_file = '/tmp/pipeline/and_003/and_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_004(self):

        cli_file = '/tmp/pipeline/and_004/and_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_005(self):

        cli_file = '/tmp/pipeline/and_005/and_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_006(self):

        cli_file = '/tmp/pipeline/and_006/and_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_007(self):

        cli_file = '/tmp/pipeline/and_007/and_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_007/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_and_008(self):

        cli_file = '/tmp/pipeline/and_008/and_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/and_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/and_008/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_001(self):

        cli_file = '/tmp/pipeline/or_001/or_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_002(self):

        cli_file = '/tmp/pipeline/or_002/or_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_003(self):

        cli_file = '/tmp/pipeline/or_003/or_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_004(self):

        cli_file = '/tmp/pipeline/or_004/or_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_005(self):

        cli_file = '/tmp/pipeline/or_005/or_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_006(self):

        cli_file = '/tmp/pipeline/or_006/or_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_007(self):

        cli_file = '/tmp/pipeline/or_007/or_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/or_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/or_007/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_or_008(self):

        cli_file = '/tmp/pipeline/or_008/or_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = 'pipeline/or_008/pcap_files/in_1.txt'
        out_pcap = 'pipeline/or_008/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 1, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(1, 1, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(2, 3, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(3, 3, in_pcap, out_pcap, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_001(self):

        cli_file = '/tmp/pipeline/xor_001/xor_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [1, 0, 3, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_002(self):

        cli_file = '/tmp/pipeline/xor_002/xor_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_003(self):

        cli_file = '/tmp/pipeline/xor_003/xor_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_004(self):

        cli_file = '/tmp/pipeline/xor_004/xor_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_005(self):

        cli_file = '/tmp/pipeline/xor_005/xor_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_006(self):

        cli_file = '/tmp/pipeline/xor_006/xor_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [1, 0, 3, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_007(self):

        cli_file = '/tmp/pipeline/xor_007/xor_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_007/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_xor_008(self):

        cli_file = '/tmp/pipeline/xor_008/xor_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/xor_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/xor_008/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_001(self):

        cli_file = '/tmp/pipeline/add_001/add_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_002(self):

        cli_file = '/tmp/pipeline/add_002/add_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_003(self):

        cli_file = '/tmp/pipeline/add_003/add_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2]
        rx_port = [1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_004(self):

        cli_file = '/tmp/pipeline/add_004/add_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_005(self):

        cli_file = '/tmp/pipeline/add_005/add_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_006(self):

        cli_file = '/tmp/pipeline/add_006/add_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_007(self):

        cli_file = '/tmp/pipeline/add_007/add_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_007/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_add_008(self):

        cli_file = '/tmp/pipeline/add_008/add_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/add_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/add_008/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_001(self):

        cli_file = '/tmp/pipeline/shl_001/shl_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_002(self):

        cli_file = '/tmp/pipeline/shl_002/shl_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_003(self):

        cli_file = '/tmp/pipeline/shl_003/shl_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_004(self):

        cli_file = '/tmp/pipeline/shl_004/shl_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_005(self):

        cli_file = '/tmp/pipeline/shl_005/shl_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_006(self):

        cli_file = '/tmp/pipeline/shl_006/shl_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_007(self):

        cli_file = '/tmp/pipeline/shl_007/shl_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_007/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shl_008(self):

        cli_file = '/tmp/pipeline/shl_008/shl_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shl_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shl_008/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_001(self):

        cli_file = '/tmp/pipeline/shr_001/shr_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_002(self):

        cli_file = '/tmp/pipeline/shr_002/shr_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_003(self):

        cli_file = '/tmp/pipeline/shr_003/shr_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_004(self):

        cli_file = '/tmp/pipeline/shr_004/shr_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_005(self):

        cli_file = '/tmp/pipeline/shr_005/shr_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_006(self):

        cli_file = '/tmp/pipeline/shr_006/shr_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_007(self):

        cli_file = '/tmp/pipeline/shr_007/shr_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_007/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_shr_008(self):

        cli_file = '/tmp/pipeline/shr_008/shr_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/shr_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/shr_008/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_001(self):

        cli_file = '/tmp/pipeline/sub_001/sub_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_002(self):

        cli_file = '/tmp/pipeline/sub_002/sub_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_003(self):

        cli_file = '/tmp/pipeline/sub_003/sub_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_004(self):

        cli_file = '/tmp/pipeline/sub_004/sub_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_005(self):

        cli_file = '/tmp/pipeline/sub_005/sub_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_006(self):

        cli_file = '/tmp/pipeline/sub_006/sub_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_007(self):

        cli_file = '/tmp/pipeline/sub_007/sub_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_007/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_sub_008(self):

        cli_file = '/tmp/pipeline/sub_008/sub_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/sub_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/sub_008/pcap_files/out_1.txt'] * 4
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_001(self):

        cli_file = '/tmp/pipeline/mov_001/mov_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/mov_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/mov_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_002(self):

        cli_file = '/tmp/pipeline/mov_002/mov_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/mov_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/mov_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_003(self):

        cli_file = '/tmp/pipeline/mov_003/mov_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/mov_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/mov_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_004(self):

        cli_file = '/tmp/pipeline/mov_004/mov_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/mov_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/mov_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_005(self):

        cli_file = '/tmp/pipeline/mov_005/mov_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = 'pipeline/mov_005/pcap_files/in_1.txt'
        out_pcap = 'pipeline/mov_005/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(1, 0, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(2, 0, in_pcap, out_pcap, "tcp")
        self.send_and_sniff_pkts(3, 0, in_pcap, out_pcap, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_007(self):

        cli_file = '/tmp/pipeline/mov_007/mov_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/mov_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/mov_007/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_mov_008(self):

        cli_file = '/tmp/pipeline/mov_008/mov_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/mov_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/mov_008/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_table_001(self):

        cli_file = '/tmp/pipeline/table_001/table_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/table_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/table_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_vxlan_001(self):

        cli_file = '/tmp/pipeline/vxlan_001/vxlan_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap_0 = 'pipeline/vxlan_001/pcap_files/in_1.txt'
        in_pcap_1 = 'pipeline/vxlan_001/pcap_files/in_2.txt'
        in_pcap_2 = 'pipeline/vxlan_001/pcap_files/in_3.txt'
        in_pcap_3 = 'pipeline/vxlan_001/pcap_files/in_4.txt'
        out_pcap_0 = 'pipeline/vxlan_001/pcap_files/out_1.txt'
        out_pcap_1 = 'pipeline/vxlan_001/pcap_files/out_2.txt'
        out_pcap_2 = 'pipeline/vxlan_001/pcap_files/out_3.txt'
        out_pcap_3 = 'pipeline/vxlan_001/pcap_files/out_4.txt'

        in_pcap = [in_pcap_0, in_pcap_1, in_pcap_2, in_pcap_3]
        out_pcap = [out_pcap_0, out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["udp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_001(self):

        cli_file = '/tmp/pipeline/dma_001/dma_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_002(self):

        cli_file = '/tmp/pipeline/dma_002/dma_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_003(self):

        cli_file = '/tmp/pipeline/dma_003/dma_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_004(self):

        cli_file = '/tmp/pipeline/dma_004/dma_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_005(self):

        cli_file = '/tmp/pipeline/dma_005/dma_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_005/pcap_files/out_1.txt'] * 4
        filters = ["vlan"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_006(self):

        cli_file = '/tmp/pipeline/dma_006/dma_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_006/pcap_files/out_1.txt'] * 4
        filters = ["udp port 4532"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_007(self):

        cli_file = '/tmp/pipeline/dma_007/dma_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_007/pcap_files/out_1.txt'] * 4
        filters = ["udp port 4532"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_dma_008(self):

        cli_file = '/tmp/pipeline/dma_008/dma_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/dma_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/dma_008/pcap_files/out_1.txt'] * 4
        filters = ["udp port 4532"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_001(self):

        cli_file = '/tmp/pipeline/jump_001/jump_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_002(self):

        cli_file = '/tmp/pipeline/jump_002/jump_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_003(self):

        cli_file = '/tmp/pipeline/jump_003/jump_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_004(self):

        cli_file = '/tmp/pipeline/jump_004/jump_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_005(self):

        cli_file = '/tmp/pipeline/jump_005/jump_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_005/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_005/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_006(self):

        cli_file = '/tmp/pipeline/jump_006/jump_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_006/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_006/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_007(self):

        cli_file = '/tmp/pipeline/jump_007/jump_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_007/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_007/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_008(self):

        cli_file = '/tmp/pipeline/jump_008/jump_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_008/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_008/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_009(self):

        cli_file = '/tmp/pipeline/jump_009/jump_009.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_009/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_009/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_010(self):

        cli_file = '/tmp/pipeline/jump_010/jump_010.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_010/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_010/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_011(self):

        cli_file = '/tmp/pipeline/jump_011/jump_011.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_011/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_011/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_012(self):

        cli_file = '/tmp/pipeline/jump_012/jump_012.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_012/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_012/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_013(self):

        cli_file = '/tmp/pipeline/jump_013/jump_013.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_013/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_013/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_014(self):

        cli_file = '/tmp/pipeline/jump_014/jump_014.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_014/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_014/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_015(self):

        cli_file = '/tmp/pipeline/jump_015/jump_015.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_015/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_015/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_016(self):

        cli_file = '/tmp/pipeline/jump_016/jump_016.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_016/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_016/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_017(self):

        cli_file = '/tmp/pipeline/jump_017/jump_017.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_017/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_017/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_018(self):

        cli_file = '/tmp/pipeline/jump_018/jump_018.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_018/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_018/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_019(self):

        cli_file = '/tmp/pipeline/jump_019/jump_019.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_019/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_019/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_020(self):

        cli_file = '/tmp/pipeline/jump_020/jump_020.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_020/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_020/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_021(self):

        cli_file = '/tmp/pipeline/jump_021/jump_021.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_021/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_021/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_022(self):

        cli_file = '/tmp/pipeline/jump_022/jump_022.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_022/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_022/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_023(self):

        cli_file = '/tmp/pipeline/jump_023/jump_023.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_023/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_023/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_024(self):

        cli_file = '/tmp/pipeline/jump_024/jump_024.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_024/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_024/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_025(self):

        cli_file = '/tmp/pipeline/jump_025/jump_025.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_025/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_025/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_026(self):

        cli_file = '/tmp/pipeline/jump_026/jump_026.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_026/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_026/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_027(self):

        cli_file = '/tmp/pipeline/jump_027/jump_027.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_027/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_027/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_028(self):

        cli_file = '/tmp/pipeline/jump_028/jump_028.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_028/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_028/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_029(self):

        cli_file = '/tmp/pipeline/jump_029/jump_029.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_029/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_029/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_030(self):

        cli_file = '/tmp/pipeline/jump_030/jump_030.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_030/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_030/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_031(self):

        cli_file = '/tmp/pipeline/jump_031/jump_031.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_031/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_031/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_032(self):

        cli_file = '/tmp/pipeline/jump_032/jump_032.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_032/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_032/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_033(self):

        cli_file = '/tmp/pipeline/jump_033/jump_033.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_033/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_033/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_034(self):

        cli_file = '/tmp/pipeline/jump_034/jump_034.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_034/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_034/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_035(self):

        cli_file = '/tmp/pipeline/jump_035/jump_035.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_035/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_035/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_036(self):

        cli_file = '/tmp/pipeline/jump_036/jump_036.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_036/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_036/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_037(self):

        cli_file = '/tmp/pipeline/jump_037/jump_037.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_037/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_037/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_038(self):

        cli_file = '/tmp/pipeline/jump_038/jump_038.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_038/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_038/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_039(self):

        cli_file = '/tmp/pipeline/jump_039/jump_039.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_039/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_039/pcap_files/out_1.txt'] * 4
        filters = [""] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_040(self):

        cli_file = '/tmp/pipeline/jump_040/jump_040.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_040/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_040/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_041(self):

        cli_file = '/tmp/pipeline/jump_041/jump_041.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_041/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_041/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_042(self):

        cli_file = '/tmp/pipeline/jump_042/jump_042.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_042/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_042/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_043(self):

        cli_file = '/tmp/pipeline/jump_043/jump_043.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_043/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_043/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_044(self):

        cli_file = '/tmp/pipeline/jump_044/jump_044.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_044/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_044/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_045(self):

        cli_file = '/tmp/pipeline/jump_045/jump_045.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_045/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_045/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_046(self):

        cli_file = '/tmp/pipeline/jump_046/jump_046.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_046/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_046/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_047(self):

        cli_file = '/tmp/pipeline/jump_047/jump_047.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_047/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_047/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_048(self):

        cli_file = '/tmp/pipeline/jump_048/jump_048.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_048/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_048/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_049(self):

        cli_file = '/tmp/pipeline/jump_049/jump_049.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_049/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_049/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_050(self):

        cli_file = '/tmp/pipeline/jump_050/jump_050.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_050/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_050/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_051(self):

        cli_file = '/tmp/pipeline/jump_051/jump_051.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_051/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_051/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_052(self):

        cli_file = '/tmp/pipeline/jump_052/jump_052.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_052/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_052/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_053(self):

        cli_file = '/tmp/pipeline/jump_053/jump_053.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_053/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_053/pcap_files/out_1.txt'] * 4
        filters = [""] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_054(self):

        cli_file = '/tmp/pipeline/jump_054/jump_054.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_054/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_054/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_jump_055(self):

        cli_file = '/tmp/pipeline/jump_055/jump_055.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/jump_055/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/jump_055/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_ckadd_001(self):

        cli_file = '/tmp/pipeline/ckadd_001/ckadd_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/ckadd_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/ckadd_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_ckadd_009(self):

        cli_file = '/tmp/pipeline/ckadd_009/ckadd_009.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/ckadd_009/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/ckadd_009/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_ckadd_010(self):

        cli_file = '/tmp/pipeline/ckadd_010/ckadd_010.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/ckadd_010/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/ckadd_010/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_cksub_001(self):

        cli_file = '/tmp/pipeline/cksub_001/cksub_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/cksub_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/cksub_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_invalidate_001(self):

        cli_file = '/tmp/pipeline/invalidate_001/invalidate_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/invalidate_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/invalidate_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_validate_001(self):

        cli_file = '/tmp/pipeline/validate_001/validate_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/validate_001/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/validate_001/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_table_002(self):

        cli_file = '/tmp/pipeline/table_002/table_002.cli'
        self.run_dpdk_app(cli_file)
        sleep(1)
        s = self.connect_cli_server()

        # empty table scenario
        in_pcap = ['pipeline/table_002/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # single rule scenario
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_2.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_2.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_2.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # two rules scenario
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_3.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_3.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_3.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # delete one rule scenario
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_4_1.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update none {} none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_4_1.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_4_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # delete all rules scenario
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_4_2.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update none {} none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_4_2.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_4_2.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # action update scenario (restore one of the previously deleted rules and check the update)
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_5_1.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = 'pipeline/table_002/pcap_files/in_5_1.txt'
        out_pcap = 'pipeline/table_002/pcap_files/out_5_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap, out_pcap, "tcp")

        # action update scenario (change the action of restored rule and check the update)
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_5_2.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_5_1.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_5_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # deafult action scenario [empty table]
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_6_1.txt'  # delete the previously added rule
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update none {} none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_6_1.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_6_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # deafult action scenario [table with one rule]
        '''
        Add key A => Lookup HIT for the right packet with the specific key associated action executed
                     Lookup MISS for any other packets with default action executed
        '''
        CMD_FILE = '/tmp/pipeline/table_002/cmd_files/cmd_6_2.txt'  # add a new rule
        CLI_CMD = 'pipeline PIPELINE0 table table_002_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_002/pcap_files/in_6_2.txt'] * 4
        out_pcap = ['pipeline/table_002/pcap_files/out_6_2.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_table_003(self):

        cli_file = '/tmp/pipeline/table_003/table_003.cli'
        self.run_dpdk_app(cli_file)
        sleep(1)
        s = self.connect_cli_server()

        # Empty table scenario
        in_pcap = ['pipeline/table_003/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # Single rule scenario
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_2.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_2.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_2.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # test two rules scenario
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_3.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_3.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_3.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # delete one rule scenario
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_4_1.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update none {} none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_4_1.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_4_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # delete all rules scenario
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_4_2.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update none {} none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_4_2.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_4_2.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # action update scenario (restore one of the previously deleted rules and check the update)
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_5_1.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = 'pipeline/table_003/pcap_files/in_5_1.txt'
        out_pcap = 'pipeline/table_003/pcap_files/out_5_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap, out_pcap, "tcp")

        # action update scenario (change the action of restored rule and check the update)
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_5_2.txt'
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_5_1.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_5_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # Default action scenario [Empty table]
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_6_1_1.txt'  # delete the previously added rule
        CMD_FILE_2 = '/tmp/pipeline/table_003/cmd_files/cmd_6_1_2.txt'  # change the default action of table
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update none {} {} \n'.format(CMD_FILE, CMD_FILE_2)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_6_1.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_6_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # Default action scenario [Table with one rule]
        '''
        Add key A => Lookup HIT for the right packet with the specific key associated action executed
                     Lookup MISS for any other packets with default action executed
        '''
        CMD_FILE = '/tmp/pipeline/table_003/cmd_files/cmd_6_2.txt'  # add a new rule
        CLI_CMD = 'pipeline PIPELINE0 table table_003_table update {} none none\n'.format(CMD_FILE)
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        in_pcap = ['pipeline/table_003/pcap_files/in_6_2.txt'] * 4
        out_pcap = ['pipeline/table_003/pcap_files/out_6_2.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_table_004(self):

        cli_file = '/tmp/pipeline/table_004/table_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/table_004/pcap_files/in_1.txt'] * 4
        out_pcap = ['pipeline/table_004/pcap_files/out_1.txt'] * 4
        filters = ["tcp"] * 4
        tx_port = [0, 1, 2, 3]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_001(self):

        cli_file = '/tmp/pipeline/reg_001/reg_001.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Read default initial value
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x0\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        # Update the register array location
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x0 0xab\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Verify updated value
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x0\n'
        self.socket_send_cmd(s, CLI_CMD, "0xab\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_002(self):

        cli_file = '/tmp/pipeline/reg_002/reg_002.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        s.close()

        # Read updated values through packet
        in_pcap_file = 'pipeline/reg_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/reg_002/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_003(self):

        cli_file = '/tmp/pipeline/reg_003/reg_003.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        s.close()

        # Read updated values through packet
        in_pcap_file = 'pipeline/reg_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/reg_003/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_004(self):

        cli_file = '/tmp/pipeline/reg_004/reg_004.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        s.close()

        # Read updated values through packet
        in_pcap_file = 'pipeline/reg_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/reg_004/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_005(self):

        cli_file = '/tmp/pipeline/reg_005/reg_005.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        s.close()

        # Read updated values through packet
        in_pcap_file = 'pipeline/reg_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/reg_005/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, "tcp")
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_006(self):

        cli_file = '/tmp/pipeline/reg_006/reg_006.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send a packet to trigger the execution of apply block
        in_pcap_file = 'pipeline/reg_006/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify written vs read values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa3a4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb3b4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_007(self):

        cli_file = '/tmp/pipeline/reg_007/reg_007.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send a packet to trigger the execution of apply block
        in_pcap_file = 'pipeline/reg_007/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify written vs read values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa3a4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb3b4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_008(self):

        cli_file = '/tmp/pipeline/reg_008/reg_008.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send a packet to trigger the execution of apply block
        in_pcap_file = 'pipeline/reg_008/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify written vs read values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa3a4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb3b4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_009(self):

        cli_file = '/tmp/pipeline/reg_009/reg_009.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0x123456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0x12345678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0x1234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0x12\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send a packet to trigger the execution of apply block
        in_pcap_file = 'pipeline/reg_009/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify written vs read values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa3a4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb3b4\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_010(self):

        cli_file = '/tmp/pipeline/reg_010/reg_010.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_010/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x6\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_011(self):

        cli_file = '/tmp/pipeline/reg_011/reg_011.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_011/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x6\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_012(self):

        cli_file = '/tmp/pipeline/reg_012/reg_012.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_012/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_013(self):

        cli_file = '/tmp/pipeline/reg_013/reg_013.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x06\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_013/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x6\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x06\n'
        self.socket_send_cmd(s, CLI_CMD, "0x9876543210987654\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_014(self):

        cli_file = '/tmp/pipeline/reg_014/reg_014.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_014/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x6\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_015(self):

        cli_file = '/tmp/pipeline/reg_015/reg_015.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_015/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x6\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_016(self):

        cli_file = '/tmp/pipeline/reg_016/reg_016.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_016/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_017(self):

        cli_file = '/tmp/pipeline/reg_017/reg_017.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_017/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_018(self):

        cli_file = '/tmp/pipeline/reg_018/reg_018.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_018/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_019(self):

        cli_file = '/tmp/pipeline/reg_019/reg_019.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_019/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_020(self):

        cli_file = '/tmp/pipeline/reg_020/reg_020.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_020/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_021(self):

        cli_file = '/tmp/pipeline/reg_021/reg_021.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_021/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_022(self):

        cli_file = '/tmp/pipeline/reg_022/reg_022.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_022/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x6\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_023(self):

        cli_file = '/tmp/pipeline/reg_023/reg_023.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_023/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_024(self):

        cli_file = '/tmp/pipeline/reg_024/reg_024.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_024/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_025(self):

        cli_file = '/tmp/pipeline/reg_025/reg_025.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Verify the default initial values of zero
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x0\npipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_025/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234567890123456\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x123456789012\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345678\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1234\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_026(self):

        cli_file = '/tmp/pipeline/reg_026/reg_026.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_026/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_027(self):

        cli_file = '/tmp/pipeline/reg_027/reg_027.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_027/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_028(self):

        cli_file = '/tmp/pipeline/reg_028/reg_028.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_028/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_029(self):

        cli_file = '/tmp/pipeline/reg_029/reg_029.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_029/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_030(self):

        cli_file = '/tmp/pipeline/reg_030/reg_030.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_030/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_031(self):

        cli_file = '/tmp/pipeline/reg_031/reg_031.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_031/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_032(self):

        cli_file = '/tmp/pipeline/reg_032/reg_032.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_032/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_033(self):

        cli_file = '/tmp/pipeline/reg_033/reg_033.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_033/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_034(self):

        cli_file = '/tmp/pipeline/reg_034/reg_034.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_034/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_035(self):

        cli_file = '/tmp/pipeline/reg_035/reg_035.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_035/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_036(self):

        cli_file = '/tmp/pipeline/reg_036/reg_036.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_036/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_037(self):

        cli_file = '/tmp/pipeline/reg_037/reg_037.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_037/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_038(self):

        cli_file = '/tmp/pipeline/reg_038/reg_038.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_038/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_039(self):

        cli_file = '/tmp/pipeline/reg_039/reg_039.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_039/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_040(self):

        cli_file = '/tmp/pipeline/reg_040/reg_040.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_040/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_041(self):

        cli_file = '/tmp/pipeline/reg_041/reg_041.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xf7 0x1f\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_041/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Update the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ace68ac468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x12345777e68a\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x124448ac\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0x10f1\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xf7\n'
        self.socket_send_cmd(s, CLI_CMD, "0x25\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_042(self):

        cli_file = '/tmp/pipeline/reg_042/reg_042.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_042/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_043(self):

        cli_file = '/tmp/pipeline/reg_043/reg_043.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_043/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_044(self):

        cli_file = '/tmp/pipeline/reg_044/reg_044.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x1a1a2a3 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7fc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0x7f 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_044/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x1a1a2a3\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7fc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0x7f\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_reg_045(self):

        cli_file = '/tmp/pipeline/reg_045/reg_045.cli'
        self.run_dpdk_app(cli_file)
        sleep(CLI_SERVER_CONNECT_DELAY)
        s = self.connect_cli_server()

        # Initialize the register array locations with required values
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xa1a2 0xff23456789012\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xb1b2 0xff5678\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xc1 0xff234\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regwr REG_ARR_1 0xd1 0xff2\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        # Send packet to DUT to update the register array
        in_pcap_file = 'pipeline/reg_045/pcap_files/in_1.txt'
        self.send_pkts(0, 0, in_pcap_file)

        # Verify whether the register array is updated with required values
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xa1a2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468acf12024\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xb1b2\n'
        self.socket_send_cmd(s, CLI_CMD, "0x1333acf0\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xc1\n'
        self.socket_send_cmd(s, CLI_CMD, "0x100468\npipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 regrd REG_ARR_1 0xd1\n'
        self.socket_send_cmd(s, CLI_CMD, "0xff8\npipeline> ")

        s.close()
        self.dut.send_expect("^C", "# ", 20)

    def test_met_001(self):

        cli_file = '/tmp/pipeline/met_001/met_001.cli'
        self.run_dpdk_app(cli_file)

        # Platinum Profile with High Packet Transmission Rate
        in_pcap = ['pipeline/met_001/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_001/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_001/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_001/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        # Platinum Profile with Low Packet Transmission Rate
        out_pcap_1 = 'pipeline/met_001/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_001/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_001/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)

        # Gold Profile with High Packet Transmission Rate
        s = self.connect_cli_server()
        CLI_CMD = 'pipeline PIPELINE0 meter profile gold add cir 460 pir 1380 cbs 100 pbs 150\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 meter MET_ARRAY_1 from 0 to 0 set profile gold\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        CLI_CMD = 'pipeline PIPELINE0 meter profile platinum delete\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")

        out_pcap_1 = 'pipeline/met_001/pcap_files/out_31.txt'
        out_pcap_2 = 'pipeline/met_001/pcap_files/out_32.txt'
        out_pcap_3 = 'pipeline/met_001/pcap_files/out_33.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        # Default Profile with High Packet Transmission Rate
        CLI_CMD = 'pipeline PIPELINE0 meter MET_ARRAY_1 from 0 to 0 reset\n'
        self.socket_send_cmd(s, CLI_CMD, "pipeline> ")
        s.close()

        out_pcap_1 = 'pipeline/met_001/pcap_files/out_41.txt'
        out_pcap_2 = 'pipeline/met_001/pcap_files/out_42.txt'
        out_pcap_3 = 'pipeline/met_001/pcap_files/out_43.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_002(self):

        cli_file = '/tmp/pipeline/met_002/met_002.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_002/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_002/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_002/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_002/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_002/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_002/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_002/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_003(self):

        cli_file = '/tmp/pipeline/met_003/met_003.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_003/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_003/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_003/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_003/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_003/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_003/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_003/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_004(self):

        cli_file = '/tmp/pipeline/met_004/met_004.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_004/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_004/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_004/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_004/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_004/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_004/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_004/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_005(self):

        cli_file = '/tmp/pipeline/met_005/met_005.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_005/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_005/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_005/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_005/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_005/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_005/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_005/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_006(self):

        cli_file = '/tmp/pipeline/met_006/met_006.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_006/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_006/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_006/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_006/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_006/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_006/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_006/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_007(self):

        cli_file = '/tmp/pipeline/met_007/met_007.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_007/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_007/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_007/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_007/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_007/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_007/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_007/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_008(self):

        cli_file = '/tmp/pipeline/met_008/met_008.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_008/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_008/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_008/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_008/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_008/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_008/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_008/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_009(self):

        cli_file = '/tmp/pipeline/met_009/met_009.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_009/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_009/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_009/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_009/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_009/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_009/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_009/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_010(self):

        cli_file = '/tmp/pipeline/met_010/met_010.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_010/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_010/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_010/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_010/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_010/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_010/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_010/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_011(self):

        cli_file = '/tmp/pipeline/met_011/met_011.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_011/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_011/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_011/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_011/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_011/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_011/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_011/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_012(self):

        cli_file = '/tmp/pipeline/met_012/met_012.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_012/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_012/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_012/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_012/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)

        out_pcap_1 = 'pipeline/met_012/pcap_files/out_21.txt'
        out_pcap_2 = 'pipeline/met_012/pcap_files/out_22.txt'
        out_pcap_3 = 'pipeline/met_012/pcap_files/out_23.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 10)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_013(self):

        cli_file = '/tmp/pipeline/met_013/met_013.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_013/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_013/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_013/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_013/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_014(self):

        cli_file = '/tmp/pipeline/met_014/met_014.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_014/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_014/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_014/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_014/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)
        self.dut.send_expect("^C", "# ", 20)

    def test_met_015(self):

        cli_file = '/tmp/pipeline/met_015/met_015.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = ['pipeline/met_015/pcap_files/in_1.txt']
        out_pcap_1 = 'pipeline/met_015/pcap_files/out_11.txt'
        out_pcap_2 = 'pipeline/met_015/pcap_files/out_12.txt'
        out_pcap_3 = 'pipeline/met_015/pcap_files/out_13.txt'
        out_pcap = [out_pcap_1, out_pcap_2, out_pcap_3]
        filters = ["tcp"] * 3
        tx_port = [0]
        rx_port = [0, 1, 2]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters, 1000)
        self.dut.send_expect("^C", "# ", 20)

    '''
    def test_tap_port_001(self):

        cli_file = '/tmp/pipeline/tap_port_001/tap_port_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = 'pipeline/tap_port_001/pcap_files/in_1.txt'
        out_pcap = 'pipeline/tap_port_001/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 0, in_pcap, out_pcap, "udp")
        self.dut.send_expect("^C", "# ", 20)
    '''

    def test_ring_port_001(self):

        cli_file = '/tmp/pipeline/ring_port_001/ring_port_001.cli'
        self.run_dpdk_app(cli_file)

        in_pcap = 'pipeline/ring_port_001/pcap_files/in_1.txt'
        out_pcap = 'pipeline/ring_port_001/pcap_files/out_1.txt'
        self.send_and_sniff_pkts(0, 1, in_pcap, out_pcap, "udp")
        self.dut.send_expect("^C", "# ", 20)

    def test_u100_001(self):

        cli_file = '/tmp/pipeline/u100_001/u100_001.cli'
        self.run_dpdk_app(cli_file)
        base_dir = 'pipeline/u100_001/pcap_files/'

        # TCP Packets
        in_pcap = ['in_1.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_11.txt', 'out_12.txt', 'out_13.txt', 'out_14.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["tcp"] * 4
        tx_port = [0]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # UDP Packets
        in_pcap = ['in_2.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_21.txt', 'out_22.txt', 'out_23.txt', 'out_24.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["udp port 200"] * 4
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # ICMP Packets
        in_pcap = ['in_3.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_31.txt', 'out_32.txt', 'out_33.txt', 'out_34.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["icmp"] * 4
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # IGMP Packets
        in_pcap = ['in_4.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_41.txt', 'out_42.txt', 'out_43.txt', 'out_44.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["igmp"] * 4
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def test_u100_002(self):

        cli_file = '/tmp/pipeline/u100_002/u100_002.cli'
        self.run_dpdk_app(cli_file)
        base_dir = 'pipeline/u100_002/pcap_files/'

        # TCP Packets
        in_pcap = ['in_1.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_11.txt', 'out_12.txt', 'out_13.txt', 'out_14.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["tcp", "vlan 16", "vlan 16", "tcp"]
        tx_port = [0]
        rx_port = [0, 1, 2, 3]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # UDP Packets
        in_pcap = ['in_2.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_21.txt', 'out_22.txt', 'out_23.txt', 'out_24.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["udp port 200", "vlan 16", "vlan 16", "udp port 200"]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # ICMP Packets
        in_pcap = ['in_3.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_31.txt', 'out_32.txt', 'out_33.txt', 'out_34.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["icmp", "vlan 16", "vlan 16", "icmp"]
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # IGMP Packets
        in_pcap = ['in_4.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_41.txt', 'out_42.txt', 'out_43.txt', 'out_44.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["igmp", "vlan 16", "vlan 16", "igmp"] * 4
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)

        # IPv6 Packets
        in_pcap = ['in_5.txt']
        in_pcap = [base_dir + s for s in in_pcap]
        out_pcap = ['out_51.txt', 'out_52.txt', 'out_53.txt', 'out_54.txt']
        out_pcap = [base_dir + s for s in out_pcap]
        filters = ["tcp"] * 4
        self.send_and_sniff_multiple(tx_port, rx_port, in_pcap, out_pcap, filters)
        self.dut.send_expect("^C", "# ", 20)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.session_secondary)
        self.dut.kill_all()

