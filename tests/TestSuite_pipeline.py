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

TIMESTAMP = re.compile(r'\d{2}\:\d{2}\:\d{2}\.\d{6}')
PAYLOAD = re.compile(r'\t0x([0-9a-fA-F]+):  ([0-9a-fA-F ]+)')

FILE_DIR = os.path.dirname(os.path.abspath(__file__)).split(os.path.sep)
DEP_DIR = os.path.sep.join(FILE_DIR[:-1]) + '/dep/'


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
        if "differ" in out:
            self.dut.send_expect('^C', '# ')
        self.verify("are identical" in out, "Output pcap files mismatch error")

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

        self.sriov_vfs_port = []
        self.session_secondary = self.dut.new_session()

        out = self.dut.build_dpdk_apps("./examples/pipeline")
        self.verify("Error" not in out, "Compilation error")
        self.app_pipeline_path = self.dut.apps_name['pipeline']
        self.app_testpmd_path = self.dut.apps_name['test-pmd']
        self.param_flow_dir = self.get_flow_direction_param_of_tcpdump()

        # update the ./dep/pipeline.tar.gz file for any new changes
        P4_PIPILINE_TAR_FILE = DEP_DIR + 'pipeline.tar.gz'
        self.tester.send_expect('rm -rf /tmp/pipeline', '# ')
        self.tester.send_expect('tar -zxf {} --directory /tmp'.format(P4_PIPILINE_TAR_FILE), "# ", 20)

        # copy the ./dep/pipeline.tar.gz file to DUT
        self.dut.send_expect('rm -rf /tmp/pipeline.tar.gz /tmp/pipeline', "# ", 20)
        self.session_secondary.copy_file_to('dep/pipeline.tar.gz', '/tmp/')
        self.dut.send_expect('tar -zxf /tmp/pipeline.tar.gz --directory /tmp', "# ", 20)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_rx_tx_001(self):
        """
        rx_tx_001: revert the received packet on the same port without any change
        """
        cli_file = '/tmp/pipeline/rx_tx_001/rx_tx_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/rx_tx_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/rx_tx_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_001(self):
        """
        extract_emit_001: revert the received packet on the same port without any change
        """
        cli_file = '/tmp/pipeline/extract_emit_001/extract_emit_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_002(self):

        cli_file = '/tmp/pipeline/extract_emit_002/extract_emit_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_003(self):

        cli_file = '/tmp/pipeline/extract_emit_003/extract_emit_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_004(self):

        cli_file = '/tmp/pipeline/extract_emit_004/extract_emit_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_005(self):

        cli_file = '/tmp/pipeline/extract_emit_005/extract_emit_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_005/pcap_files/out_1.txt'
        filters = "vlan"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_006(self):

        cli_file = '/tmp/pipeline/extract_emit_006/extract_emit_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_006/pcap_files/out_1.txt'
        filters = "udp port 4789"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_007(self):

        cli_file = '/tmp/pipeline/extract_emit_007/extract_emit_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_007/pcap_files/out_1.txt'
        filters = "udp port 4789"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_008(self):

        cli_file = '/tmp/pipeline/extract_emit_008/extract_emit_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_008/pcap_files/out_1.txt'
        filters = "udp port 4789"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_extract_emit_009(self):

        cli_file = '/tmp/pipeline/extract_emit_009/extract_emit_009.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/extract_emit_009/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/extract_emit_009/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_001(self):

        cli_file = '/tmp/pipeline/and_001/and_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_002(self):

        cli_file = '/tmp/pipeline/and_002/and_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 0, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 0, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 0, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_003(self):

        cli_file = '/tmp/pipeline/and_003/and_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_004(self):

        cli_file = '/tmp/pipeline/and_004/and_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_005(self):

        cli_file = '/tmp/pipeline/and_005/and_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_006(self):

        cli_file = '/tmp/pipeline/and_006/and_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_007(self):

        cli_file = '/tmp/pipeline/and_007/and_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_007/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_and_008(self):

        cli_file = '/tmp/pipeline/and_008/and_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/and_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/and_008/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_001(self):

        cli_file = '/tmp/pipeline/or_001/or_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_002(self):

        cli_file = '/tmp/pipeline/or_002/or_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_003(self):

        cli_file = '/tmp/pipeline/or_003/or_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_004(self):

        cli_file = '/tmp/pipeline/or_004/or_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_005(self):

        cli_file = '/tmp/pipeline/or_005/or_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_006(self):

        cli_file = '/tmp/pipeline/or_006/or_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_007(self):

        cli_file = '/tmp/pipeline/or_007/or_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_007/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_or_008(self):

        cli_file = '/tmp/pipeline/or_008/or_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/or_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/or_008/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 3, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_001(self):

        cli_file = '/tmp/pipeline/xor_001/xor_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/xor_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 0, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 3, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 2, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_002(self):

        cli_file = '/tmp/pipeline/xor_002/xor_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/xor_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_003(self):

        cli_file = '/tmp/pipeline/xor_003/xor_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/xor_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_004(self):

        cli_file = '/tmp/pipeline/xor_004/xor_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/xor_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_005(self):

        cli_file = '/tmp/pipeline/xor_005/xor_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/xor_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_006(self):
        """
        find entry in the table based on the des mac address,
        then update the src mac address to the mac address in the table.
        """

        cli_file = '/tmp/pipeline/xor_006/xor_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        in_pcap_file = 'pipeline/xor_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_006/pcap_files/out_1.txt'
        filters = "tcp"

        # rule 0 test
        sniff_pkts = self.send_and_sniff_pkts(0, 1, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 0, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 3, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 2, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_007(self):
        """
        find entry in the table based on the des mac address,
        then update the src mac address to the mac address in the table.
        """

        cli_file = '/tmp/pipeline/xor_007/xor_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        in_pcap_file = 'pipeline/xor_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_007/pcap_files/out_1.txt'
        filters = "tcp"

        # rule 0 test
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_xor_008(self):

        cli_file = '/tmp/pipeline/xor_008/xor_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/xor_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/xor_008/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_001(self):

        cli_file = '/tmp/pipeline/add_001/add_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_002(self):

        cli_file = '/tmp/pipeline/add_002/add_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_003(self):

        cli_file = '/tmp/pipeline/add_003/add_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 2, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_004(self):

        cli_file = '/tmp/pipeline/add_004/add_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_005(self):

        cli_file = '/tmp/pipeline/add_005/add_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_006(self):

        cli_file = '/tmp/pipeline/add_006/add_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_007(self):

        cli_file = '/tmp/pipeline/add_007/add_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_007/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_add_008(self):

        cli_file = '/tmp/pipeline/add_008/add_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/add_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/add_008/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_001(self):

        cli_file = '/tmp/pipeline/shl_001/shl_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_002(self):

        cli_file = '/tmp/pipeline/shl_002/shl_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_003(self):

        cli_file = '/tmp/pipeline/shl_003/shl_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_004(self):

        cli_file = '/tmp/pipeline/shl_004/shl_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_005(self):

        cli_file = '/tmp/pipeline/shl_005/shl_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_006(self):

        cli_file = '/tmp/pipeline/shl_006/shl_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_007(self):

        cli_file = '/tmp/pipeline/shl_007/shl_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_007/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shl_008(self):

        cli_file = '/tmp/pipeline/shl_008/shl_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shl_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shl_008/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_001(self):

        cli_file = '/tmp/pipeline/shr_001/shr_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_002(self):

        cli_file = '/tmp/pipeline/shr_002/shr_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_003(self):

        cli_file = '/tmp/pipeline/shr_003/shr_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_004(self):

        cli_file = '/tmp/pipeline/shr_004/shr_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_005(self):

        cli_file = '/tmp/pipeline/shr_005/shr_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_006(self):

        cli_file = '/tmp/pipeline/shr_006/shr_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_007(self):

        cli_file = '/tmp/pipeline/shr_007/shr_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_007/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_shr_008(self):

        cli_file = '/tmp/pipeline/shr_008/shr_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/shr_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/shr_008/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_001(self):

        cli_file = '/tmp/pipeline/sub_001/sub_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_002(self):

        cli_file = '/tmp/pipeline/sub_002/sub_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_003(self):

        cli_file = '/tmp/pipeline/sub_003/sub_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_004(self):

        cli_file = '/tmp/pipeline/sub_004/sub_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_005(self):

        cli_file = '/tmp/pipeline/sub_005/sub_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_006(self):

        cli_file = '/tmp/pipeline/sub_006/sub_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_007(self):

        cli_file = '/tmp/pipeline/sub_007/sub_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_007/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_sub_008(self):

        cli_file = '/tmp/pipeline/sub_008/sub_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/sub_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/sub_008/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_001(self):

        cli_file = '/tmp/pipeline/mov_001/mov_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/mov_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_002(self):
        """
        mov_002: swap destination and source MAC address of packets received on port
        """
        cli_file = '/tmp/pipeline/mov_002/mov_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/mov_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_003(self):

        cli_file = '/tmp/pipeline/mov_003/mov_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/mov_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_004(self):
        """
        find entry in the table based on the des mac address,
        then update the src mac address to the mac address in the table.
        """

        cli_file = '/tmp/pipeline/mov_004/mov_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        in_pcap_file = 'pipeline/mov_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_004/pcap_files/out_1.txt'
        filters = "tcp"

        # rule 0 test
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_005(self):
        """
        find entry in the table based on the des mac address,
        then update the src mac address to the mac address in the table.
        """

        cli_file = '/tmp/pipeline/mov_005/mov_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        in_pcap_file = 'pipeline/mov_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_005/pcap_files/out_1.txt'
        filters = "tcp"

        # rule 0 test
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 0, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 0, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 0, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_007(self):
        """
        find entry in the table based on the des mac address,
        then update the src mac address to the mac address in the table.
        """

        cli_file = '/tmp/pipeline/mov_007/mov_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        in_pcap_file = 'pipeline/mov_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_007/pcap_files/out_1.txt'
        filters = "tcp"

        # rule 0 test
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 0, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 0, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 0, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_mov_008(self):
        """
        find entry in the table based on the des mac address,
        then update the src mac address to the mac address in the table.
        """

        cli_file = '/tmp/pipeline/mov_008/mov_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        in_pcap_file = 'pipeline/mov_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/mov_008/pcap_files/out_1.txt'
        filters = "tcp"

        # rule 0 test
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_table_001(self):

        cli_file = '/tmp/pipeline/table_001/table_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/table_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/table_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_vxlan_001(self):
        """
        example application: vxlan pipeline
        """
        cli_file = '/tmp/pipeline/vxlan_001/vxlan_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/vxlan_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/vxlan_001/pcap_files/out_1.txt'
        filters = "udp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        in_pcap_file = 'pipeline/vxlan_001/pcap_files/in_2.txt'
        out_pcap_file = 'pipeline/vxlan_001/pcap_files/out_2.txt'
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        in_pcap_file = 'pipeline/vxlan_001/pcap_files/in_3.txt'
        out_pcap_file = 'pipeline/vxlan_001/pcap_files/out_3.txt'
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        in_pcap_file = 'pipeline/vxlan_001/pcap_files/in_4.txt'
        out_pcap_file = 'pipeline/vxlan_001/pcap_files/out_4.txt'
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_001(self):
        """
        example application: vxlan pipeline
        """
        cli_file = '/tmp/pipeline/dma_001/dma_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test

        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_002(self):

        cli_file = '/tmp/pipeline/dma_002/dma_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_003(self):

        cli_file = '/tmp/pipeline/dma_003/dma_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_004(self):

        cli_file = '/tmp/pipeline/dma_004/dma_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_005(self):

        cli_file = '/tmp/pipeline/dma_005/dma_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_005/pcap_files/out_1.txt'
        filters = "vlan"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_006(self):

        cli_file = '/tmp/pipeline/dma_006/dma_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_006/pcap_files/out_1.txt'
        filters = "udp port 4532"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_007(self):

        cli_file = '/tmp/pipeline/dma_007/dma_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_007/pcap_files/out_1.txt'
        filters = "udp port 4532"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_dma_008(self):

        cli_file = '/tmp/pipeline/dma_008/dma_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/dma_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/dma_008/pcap_files/out_1.txt'
        filters = "udp port 4532"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_001(self):

        cli_file = '/tmp/pipeline/jump_001/jump_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_002(self):

        cli_file = '/tmp/pipeline/jump_002/jump_002.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_002/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_002/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_003(self):

        cli_file = '/tmp/pipeline/jump_003/jump_003.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_003/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_003/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_004(self):

        cli_file = '/tmp/pipeline/jump_004/jump_004.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_004/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_004/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_005(self):

        cli_file = '/tmp/pipeline/jump_005/jump_005.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_005/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_005/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_006(self):

        cli_file = '/tmp/pipeline/jump_006/jump_006.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_006/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_006/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_007(self):

        cli_file = '/tmp/pipeline/jump_007/jump_007.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_007/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_007/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_008(self):

        cli_file = '/tmp/pipeline/jump_008/jump_008.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_008/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_008/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_009(self):

        cli_file = '/tmp/pipeline/jump_009/jump_009.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_009/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_009/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_010(self):

        cli_file = '/tmp/pipeline/jump_010/jump_010.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_010/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_010/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_011(self):

        cli_file = '/tmp/pipeline/jump_011/jump_011.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_011/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_011/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_012(self):

        cli_file = '/tmp/pipeline/jump_012/jump_012.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_012/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_012/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_013(self):

        cli_file = '/tmp/pipeline/jump_013/jump_013.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_013/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_013/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_014(self):

        cli_file = '/tmp/pipeline/jump_014/jump_014.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_014/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_014/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_015(self):

        cli_file = '/tmp/pipeline/jump_015/jump_015.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_015/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_015/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_016(self):

        cli_file = '/tmp/pipeline/jump_016/jump_016.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_016/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_016/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_017(self):

        cli_file = '/tmp/pipeline/jump_017/jump_017.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_017/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_017/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_018(self):

        cli_file = '/tmp/pipeline/jump_018/jump_018.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_018/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_018/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_019(self):

        cli_file = '/tmp/pipeline/jump_019/jump_019.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_019/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_019/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_020(self):

        cli_file = '/tmp/pipeline/jump_020/jump_020.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_020/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_020/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_021(self):

        cli_file = '/tmp/pipeline/jump_021/jump_021.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_021/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_021/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_022(self):

        cli_file = '/tmp/pipeline/jump_022/jump_022.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_022/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_022/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_023(self):

        cli_file = '/tmp/pipeline/jump_023/jump_023.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_023/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_023/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_024(self):

        cli_file = '/tmp/pipeline/jump_024/jump_024.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_024/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_024/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_025(self):

        cli_file = '/tmp/pipeline/jump_025/jump_025.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_025/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_025/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_026(self):

        cli_file = '/tmp/pipeline/jump_026/jump_026.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_026/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_026/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_027(self):

        cli_file = '/tmp/pipeline/jump_027/jump_027.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_027/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_027/pcap_files/out_1.txt'
        filters = ""
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_028(self):

        cli_file = '/tmp/pipeline/jump_028/jump_028.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_028/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_028/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_029(self):

        cli_file = '/tmp/pipeline/jump_029/jump_029.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_029/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_029/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_030(self):

        cli_file = '/tmp/pipeline/jump_030/jump_030.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_030/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_030/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_031(self):

        cli_file = '/tmp/pipeline/jump_031/jump_031.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_031/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_031/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_032(self):

        cli_file = '/tmp/pipeline/jump_032/jump_032.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_032/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_032/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_033(self):

        cli_file = '/tmp/pipeline/jump_033/jump_033.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_033/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_033/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_034(self):

        cli_file = '/tmp/pipeline/jump_034/jump_034.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_034/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_034/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_035(self):

        cli_file = '/tmp/pipeline/jump_035/jump_035.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_035/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_035/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_036(self):

        cli_file = '/tmp/pipeline/jump_036/jump_036.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_036/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_036/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_037(self):

        cli_file = '/tmp/pipeline/jump_037/jump_037.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_037/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_037/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_038(self):

        cli_file = '/tmp/pipeline/jump_038/jump_038.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_038/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_038/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_039(self):

        cli_file = '/tmp/pipeline/jump_039/jump_039.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_039/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_039/pcap_files/out_1.txt'
        filters = ""
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_040(self):

        cli_file = '/tmp/pipeline/jump_040/jump_040.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_040/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_040/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_041(self):

        cli_file = '/tmp/pipeline/jump_041/jump_041.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_041/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_041/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_042(self):

        cli_file = '/tmp/pipeline/jump_042/jump_042.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_042/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_042/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_043(self):

        cli_file = '/tmp/pipeline/jump_043/jump_043.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_043/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_043/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_044(self):

        cli_file = '/tmp/pipeline/jump_044/jump_044.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_044/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_044/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_045(self):

        cli_file = '/tmp/pipeline/jump_045/jump_045.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_045/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_045/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_046(self):

        cli_file = '/tmp/pipeline/jump_046/jump_046.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_046/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_046/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_047(self):

        cli_file = '/tmp/pipeline/jump_047/jump_047.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_047/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_047/pcap_files/out_1.txt'
        filters = ""
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_048(self):

        cli_file = '/tmp/pipeline/jump_048/jump_048.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_048/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_048/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_049(self):

        cli_file = '/tmp/pipeline/jump_049/jump_049.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_049/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_049/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_050(self):

        cli_file = '/tmp/pipeline/jump_050/jump_050.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_050/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_050/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_051(self):

        cli_file = '/tmp/pipeline/jump_051/jump_051.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_051/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_051/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_052(self):

        cli_file = '/tmp/pipeline/jump_052/jump_052.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_052/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_052/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_053(self):

        cli_file = '/tmp/pipeline/jump_053/jump_053.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_053/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_053/pcap_files/out_1.txt'
        filters = ""
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_054(self):

        cli_file = '/tmp/pipeline/jump_054/jump_054.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_054/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_054/pcap_files/out_1.txt'
        filters = ""
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_jump_055(self):

        cli_file = '/tmp/pipeline/jump_055/jump_055.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/jump_055/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/jump_055/pcap_files/out_1.txt'
        filters = ""
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_ckadd_001(self):

        cli_file = '/tmp/pipeline/ckadd_001/ckadd_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/ckadd_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/ckadd_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_ckadd_009(self):

        cli_file = '/tmp/pipeline/ckadd_009/ckadd_009.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/ckadd_009/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/ckadd_009/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_ckadd_010(self):

        cli_file = '/tmp/pipeline/ckadd_010/ckadd_010.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/ckadd_010/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/ckadd_010/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_cksub_001(self):

        cli_file = '/tmp/pipeline/cksub_001/cksub_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/cksub_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/cksub_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_invalidate_001(self):

        cli_file = '/tmp/pipeline/invalidate_001/invalidate_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/invalidate_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/invalidate_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_validate_001(self):

        cli_file = '/tmp/pipeline/validate_001/validate_001.cli'

        cmd = "sed -i -e 's/0000:00:04.0/%s/' {}".format(cli_file) % self.dut_p0_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:05.0/%s/' {}".format(cli_file) % self.dut_p1_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:06.0/%s/' {}".format(cli_file) % self.dut_p2_pci
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i -e 's/0000:00:07.0/%s/' {}".format(cli_file) % self.dut_p3_pci
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = " -w {0} -w {1} -w {2} -w {3} "\
                    .format(self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci)

        cmd = "{0} -c 0x3 -n 4 {1} -- -s {2}".format(self.app_pipeline_path, DUT_PORTS, cli_file)
        self.dut.send_expect(cmd, "PIPELINE0 enable", 60)

        # rule 0 test
        in_pcap_file = 'pipeline/validate_001/pcap_files/in_1.txt'
        out_pcap_file = 'pipeline/validate_001/pcap_files/out_1.txt'
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, in_pcap_file, out_pcap_file, filters)

        # rule 1 test
        sniff_pkts = self.send_and_sniff_pkts(1, 1, in_pcap_file, out_pcap_file, filters)

        # rule 2 test
        sniff_pkts = self.send_and_sniff_pkts(2, 2, in_pcap_file, out_pcap_file, filters)

        # rule 3 test
        sniff_pkts = self.send_and_sniff_pkts(3, 3, in_pcap_file, out_pcap_file, filters)

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

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

