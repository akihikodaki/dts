# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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
Test softnic API in DPDK.
"""

import utils
import string
import re
import time
from settings import HEADER_SIZE
import os
from pktgen import PacketGeneratorHelper
from test_case import TestCase
from pmd_output import PmdOutput


class TestSoftnic(TestCase):

    def set_up_all(self):

        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()
        self.dut_ports = self.dut.get_ports(self.nic)

        # Verify that enough ports are available
        self.verify(len(ports) >= 1, "Insufficient ports for testing")
        self.def_driver = self.dut.ports_info[ports[0]]['port'].get_nic_driver()
        self.ports_socket = self.dut.get_numa_id(ports[0])
        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/1C/1T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        global P0
        P0 = ports[0]

        self.txItf = self.tester.get_interface(self.tester.get_local_port(P0))
        self.dmac = self.dut.get_mac_address(P0)
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['udp']

        # need change config files
        self.root_path = "/tmp/"
        self.firmware = r"dep/firmware.cli"
        self.tm_firmware = r"dep/tm_firmware.cli"
        self.nat_firmware = r"dep/nat_firmware.cli"
        self.dut.session.copy_file_to(self.firmware, self.root_path)
        self.dut.session.copy_file_to(self.tm_firmware, self.root_path)
        self.dut.session.copy_file_to(self.nat_firmware, self.root_path)
        self.eal_param = " -w %s" % self.dut.ports_info[0]['pci']
        self.path = self.dut.apps_name['test-pmd']
        self.pmdout = PmdOutput(self.dut)
        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(
                                os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.dut.bind_interfaces_linux(self.drivername, [ports[0]])

    def set_up(self):
        """
        Run before each test case.
        """
    def change_config_file(self, file_name):
        self.dut.send_expect("sed -i -e '4c link LINK0 dev %s' %s" % (self.dut.ports_info[0]['pci'], self.root_path+file_name), "#")
        self.dut.send_expect("sed -i -e 's/thread [0-9]/thread 2/g' %s" % self.root_path+file_name, "#")

    def test_perf_softnic_performance(self):
        self.frame_size = [64, 128, 256, 512, 1024, 1280, 1518]
        self.change_config_file('firmware.cli')
        # 10G nic pps(M)
        expect_pps = [14, 8, 4, 2, 1, 0.9, 0.8]

        self.pmdout.start_testpmd(list(range(3)), "--forward-mode=softnic --portmask=0x2",
                                  eal_param="-s 0x4 %s --vdev 'net_softnic0,firmware=/tmp/%s,cpu_id=1,conn_port=8086'"
                                            % (self.eal_param, 'firmware.cli'))
        self.dut.send_expect("start", "testpmd>")
        rx_port = self.tester.get_local_port(0)
        tx_port = self.tester.get_local_port(0)
        n = 0
        for frame in self.frame_size:
            payload_size = frame - self.headers_size
            tgen_input = []
            pcap = os.sep.join([self.output_path, "test.pcap"])
            pkt = "Ether(dst='%s')/IP()/UDP()/Raw(load='x'*%d)" % (self.dmac, payload_size)
            self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, pkt))
            tgen_input.append((tx_port, rx_port, pcap))
            self.tester.scapy_execute()
            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100, None, self.tester.pktgen)
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
            pps = pps / 1000000.0
            self.verify(pps > 0, 'No traffic detected')
            self.verify(pps > expect_pps[n], 'No traffic detected')
            n = n + 1

    def test_perf_shaping_for_pipe(self):
        self.change_config_file('tm_firmware.cli')
        self.pmdout.start_testpmd(list(range(3)), "--forward-mode=softnic --portmask=0x2",
                                  eal_param="-s 0x4 %s --vdev 'net_softnic0,firmware=/tmp/%s,cpu_id=1,conn_port=8086'"
                                            % (self.eal_param, 'tm_firmware.cli'))
        self.dut.send_expect("start", "testpmd>")
        rx_port = self.tester.get_local_port(0)
        pkts = ["Ether(dst='%s')/IP(dst='100.0.0.0')/UDP()/Raw(load='x'*(64 - %s))", "Ether(dst='%s')/IP(dst='100.0.15.255')/UDP()/Raw(load='x'*(64 - %s))", "Ether(dst='%s')/IP(dst='100.0.4.0')/UDP()/Raw(load='x'*(64 - %s))"]
        except_bps_range = [1700000, 2000000]

        for i in range(3):
                tgen_input = []
                pcap = os.sep.join([self.output_path, "test.pcap"])
                pkt = pkts[i] % (self.dmac, self.headers_size)
                self.tester.scapy_append('wrpcap("%s", [%s])' % (pcap, pkt))
                self.tester.scapy_execute()
                if i == 2:
                    for j in range(16):
                        pk = "Ether(dst='%s')/IP(dst='100.0.15.%d')/UDP()/Raw(load='x'*(64 - %s))" % (self.dmac, j, self.headers_size)
                        self.tester.scapy_append('wrpcap("%s/test_%d.pcap", [%s])' % (self.output_path, j, pk))
                        self.tester.scapy_execute()
                        tgen_input.append((rx_port, rx_port, "%s/test_%d.pcap" % (self.output_path, j)))
                else:
                    tgen_input.append((rx_port, rx_port, pcap))
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100, None, self.tester.pktgen)
                bps, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
                if i == 2:
                    self.verify(except_bps_range[1]*16 > bps > except_bps_range[0]*16, 'No traffic detected')
                else:
                    self.verify(except_bps_range[1] > bps > except_bps_range[0], 'No traffic detected')

    def test_nat(self):
        self.change_config_file('nat_firmware.cli')
        expect_ips = ['192.168.0.1.5000', '192.168.0.2.5001']
        ips = ['100.0.0.1', '100.0.0.2']
        pkt_location = ['src', 'dst']
        pkt_type = ['tcp', 'udp']
        for t in pkt_type:
            for i in range(2):
                self.dut.send_expect("sed -i -e '12c table action profile AP0 ipv4 offset 270 fwd nat %s proto %s' %s" % (pkt_location[i], t, self.root_path + 'nat_firmware.cli'), "#")
                self.pmdout.start_testpmd(list(range(3)), "--forward-mode=softnic --portmask=0x2",
                                          eal_param="-s 0x4 %s --vdev 'net_softnic0,firmware=/tmp/%s,cpu_id=1,conn_port=8086'" % (
                                          self.eal_param, 'nat_firmware.cli'))
                if self.nic in ["columbiaville_100g", "columbiaville_25g", "columbiaville_25gx2"]:
                    self.dut.send_expect("set fwd mac", "testpmd>")
                self.dut.send_expect("start", "testpmd>")
                # src ip tcp
                for j in range(2):
                    out = self.scapy_send_packet(pkt_location[i], ips[j], t)
                    self.verify(expect_ips[j] in out, 'fail to receive expect packet')
                self.dut.send_expect("quit", "# ")
                time.sleep(1)

    def scapy_send_packet(self, pkt_location, ip, pkt_type):
        self.tester.scapy_foreground()
        pkt = "Ether(dst='%s')/IP(dst='%s')/" % (self.dmac, ip)
        if pkt_type == 'tcp':
            pkt = pkt + "TCP()/Raw(load='x'*20)"
        else:
            pkt = pkt + "UDP()/Raw(load='x'*20)"

        self.tester.scapy_append('sendp([%s], iface="%s")' % (pkt, self.txItf))
        self.start_tcpdump(self.txItf)
        self.tester.scapy_execute()
        out = self.get_tcpdump_package()
        return out

    def get_tcpdump_package(self):
        time.sleep(4)
        self.tester.send_expect("killall tcpdump", "#")
        out = self.tester.send_expect("tcpdump -A -nn -e -vv -r getPackageByTcpdump.cap |grep '192.168'", "#")
        return out

    def start_tcpdump(self, rxItf):
        self.tester.send_expect("rm -rf getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -A -nn -e -vv -w getPackageByTcpdump.cap -i %s 2> /dev/null& " % self.txItf, "#")
        time.sleep(4)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect('quit', '# ')

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.bind_interfaces_linux(driver=self.def_driver, nics_to_bind=self.dut.get_ports())
