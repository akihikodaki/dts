# BSD LICENSE
#
# Copyright(c) 2010-2018 Intel Corporation. All rights reserved.
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
import random
import re
import time
from time import sleep

import scapy.layers.inet
from scapy.arch import get_if_hwaddr
from scapy.layers.inet import ICMP, IP, TCP, UDP, Ether
from scapy.layers.l2 import ARP, GRE, Dot1Q
from scapy.layers.sctp import SCTP, SCTPChunkData
from scapy.packet import Raw, bind_layers
from scapy.route import *
from scapy.sendrecv import sendp, sniff

# from scapy.all import conf
from scapy.utils import hexstr, rdpcap, wrpcap

import framework.utils as utils
from framework.crb import Crb
from framework.dut import Dut
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.project_dpdk import DPDKdut
from framework.settings import DRIVERS, HEADER_SIZE
from framework.test_case import TestCase
from framework.virt_dut import VirtDut


class TestIPPipeline(TestCase):
    def get_flow_direction_param_of_tcpdump(self):
        """
        get flow dirction param depend on tcpdump version
        """
        param = ""
        direct_param = r"(\s+)\[ (\S+) in\|out\|inout \]"
        out = self.tester.send_expect("tcpdump -h", "# ")
        for line in out.split("\n"):
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
        command = "rm -f /tmp/tcpdump_{0}.pcap".format(interface)
        self.tester.send_expect(command, "#")
        command = "tcpdump -n -e {0} -w /tmp/tcpdump_{1}.pcap -i {1} {2} 2>/tmp/tcpdump_{1}.out &".format(
            self.param_flow_dir, interface, filters
        )
        self.tester.send_expect(command, "# ")

    def tcpdump_stop_sniff(self):
        """
        Stops the tcpdump process running in the background.
        """
        self.tester.send_expect("killall tcpdump", "# ")
        # For the [pid]+ Done tcpdump... message after killing the process
        sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', "# ")
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

    def send_and_sniff_pkts(self, from_port, to_port, pcap_file, filters="", count=1):
        """
        Sent pkts that read from the pcap_file.
        Return the sniff pkts.
        """
        tx_port = self.tester.get_local_port(self.dut_ports[from_port])
        rx_port = self.tester.get_local_port(self.dut_ports[to_port])

        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)

        self.tcpdump_start_sniff(rx_interface, filters)

        # Prepare the pkts to be sent
        self.tester.scapy_foreground()
        self.tester.scapy_append('pkt = rdpcap("%s")' % (pcap_file))
        self.tester.scapy_append(
            'sendp(pkt, iface="%s", count=%d)' % (tx_interface, count)
        )
        self.tester.scapy_execute()

        self.tcpdump_stop_sniff()

        return self.read_pcap_file("/tmp/tcpdump_%s.pcap" % rx_interface)

    def setup_env(self, port_nums, driver):
        """
        This is to set up vf environment.
        The pf is bound to dpdk driver.
        """
        self.dut.send_expect("modprobe vfio-pci", "# ")
        if driver == "default":
            for port_id in self.dut_ports:
                port = self.dut.ports_info[port_id]["port"]
                port.bind_driver()
        # one PF generate one VF
        for port_num in range(port_nums):
            self.dut.generate_sriov_vfs_by_port(self.dut_ports[port_num], 1, driver)
            self.sriov_vfs_port.append(
                self.dut.ports_info[self.dut_ports[port_num]]["vfs_port"]
            )
        if driver == "default":
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf0_interface, self.vf0_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf1_interface, self.vf1_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf2_interface, self.vf2_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf3_interface, self.vf3_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf0_interface, "# ", 3
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf1_interface, "# ", 3
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf2_interface, "# ", 3
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf3_interface, "# ", 3
            )

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
        self.verify(
            len(self.dut_ports) >= self.port_nums,
            "Insufficient ports for speed testing",
        )

        self.dut_p0_pci = self.dut.get_port_pci(self.dut_ports[0])
        self.dut_p1_pci = self.dut.get_port_pci(self.dut_ports[1])
        self.dut_p2_pci = self.dut.get_port_pci(self.dut_ports[2])
        self.dut_p3_pci = self.dut.get_port_pci(self.dut_ports[3])

        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.dut_p1_mac = self.dut.get_mac_address(self.dut_ports[1])
        self.dut_p2_mac = self.dut.get_mac_address(self.dut_ports[2])
        self.dut_p3_mac = self.dut.get_mac_address(self.dut_ports[3])

        self.pf0_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf1_interface = self.dut.ports_info[self.dut_ports[1]]["intf"]
        self.pf2_interface = self.dut.ports_info[self.dut_ports[2]]["intf"]
        self.pf3_interface = self.dut.ports_info[self.dut_ports[3]]["intf"]

        self.vf0_mac = "00:11:22:33:44:55"
        self.vf1_mac = "00:11:22:33:44:56"
        self.vf2_mac = "00:11:22:33:44:57"
        self.vf3_mac = "00:11:22:33:44:58"

        ports = [self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci]
        self.eal_para = self.dut.create_eal_parameters(
            cores=list(range(2)), ports=ports
        )
        self.sriov_vfs_port = []
        self.session_secondary = self.dut.new_session()

        out = self.dut.build_dpdk_apps("./examples/ip_pipeline")
        self.verify("Error" not in out, "Compilation error")
        self.app_ip_pipline_path = self.dut.apps_name["ip_pipeline"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.param_flow_dir = self.get_flow_direction_param_of_tcpdump()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_routing_pipeline(self):
        """
        routing pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/route.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "30:31:32:33:34:35", 60)

        # rule 0 test
        pcap_file = "/tmp/route_0.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.0.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.0.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("a0:a1:a2:a3:a4:a5" in dst_mac_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/route_1.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.64.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.64.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("b0:b1:b2:b3:b4:b5" in dst_mac_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/route_2.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.128.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.128.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("c0:c1:c2:c3:c4:c5" in dst_mac_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/route_3.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.192.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.192.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("d0:d1:d2:d3:d4:d5" in dst_mac_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_firewall_pipeline(self):
        """
        firewall pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/firewall.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 3", 60)

        # rule 0 test
        pcap_file = "/tmp/fw_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.0.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.0.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.0.0.1" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/fw_1.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.64.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.64.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.64.0.1" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/fw_2.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.128.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.128.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.128.0.1" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/fw_3.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.192.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.192.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.192.0.1" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_flow_pipeline(self):
        """
        flow pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/flow.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 3", 60)

        # rule 0 test
        pcap_file = "/tmp/fl_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/fl_1.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/fl_2.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/fl_3.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_l2fwd_pipeline(self):
        """
        l2fwd pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/l2fwd.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 2", 60)

        # rule 0 test
        pcap_file = "/tmp/pt_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/pt_1.pcap"
        pkt = [
            Ether(dst=self.dut_p1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/pt_2.pcap"
        pkt = [
            Ether(dst=self.dut_p2_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(2, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/pt_3.pcap"
        pkt = [
            Ether(dst=self.dut_p3_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(3, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_pfdpdk_vf_l2fwd_pipeline(self):
        """
        VF l2fwd pipeline, PF bound to DPDK driver
        """
        self.setup_env(self.port_nums, driver=self.drivername)
        self.dut.send_expect(
            "sed -i '/^link LINK/d' ./examples/ip_pipeline/examples/l2fwd.cli", "# ", 20
        )
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK3 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[3][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK2 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[2][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK1 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[1][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK0 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[0][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PF_PORTS = [
            self.dut_p0_pci,
            self.dut_p1_pci,
            self.dut_p2_pci,
            self.dut_p3_pci,
        ]
        PF_SCRIPT_FILE = "--socket-mem 1024,1024"

        DUT_VF_PORTS = [
            self.sriov_vfs_port[0][0].pci,
            self.sriov_vfs_port[1][0].pci,
            self.sriov_vfs_port[2][0].pci,
            self.sriov_vfs_port[3][0].pci,
        ]
        VF_SCRIPT_FILE = "./examples/ip_pipeline/examples/l2fwd.cli"

        pf_eal_para = self.dut.create_eal_parameters(
            cores=list(range(4, 8)), prefix="pf", ports=DUT_PF_PORTS
        )
        pf_cmd = "{0} {1} {2} -- -i".format(
            self.app_testpmd_path, pf_eal_para, PF_SCRIPT_FILE
        )
        self.dut.send_expect(pf_cmd, "testpmd> ", 60)
        self.dut.send_expect("set vf mac addr 0 0 %s" % self.vf0_mac, "testpmd> ", 30)
        self.dut.send_expect("set vf mac addr 1 0 %s" % self.vf1_mac, "testpmd> ", 30)
        self.dut.send_expect("set vf mac addr 2 0 %s" % self.vf2_mac, "testpmd> ", 30)
        self.dut.send_expect("set vf mac addr 3 0 %s" % self.vf3_mac, "testpmd> ", 30)

        vf_eal_para = self.dut.create_eal_parameters(
            cores=list(range(2)), ports=DUT_VF_PORTS
        )
        vf_cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, vf_eal_para, VF_SCRIPT_FILE
        )
        self.session_secondary.send_expect(vf_cmd, "fwd port 2", 60)

        # rule 0 test
        pcap_file = "/tmp/pt_0.pcap"
        pkt = [
            Ether(dst=self.vf0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/pt_1.pcap"
        pkt = [
            Ether(dst=self.vf1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/pt_2.pcap"
        pkt = [
            Ether(dst=self.vf2_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(2, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/pt_3.pcap"
        pkt = [
            Ether(dst=self.vf3_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(3, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        self.destroy_env(self.port_nums, driver=self.drivername)

    def test_pfkernel_vf_l2fwd_pipeline(self):
        """
        VF l2fwd pipeline, PF bound to kernel driver
        """
        self.setup_env(self.port_nums, driver="default")
        self.dut.send_expect(
            "sed -i '/^link LINK/d' ./examples/ip_pipeline/examples/l2fwd.cli", "# ", 20
        )
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK3 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[3][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK2 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[2][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK1 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[1][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK0 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[0][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_VF_PORTS = [
            self.sriov_vfs_port[0][0].pci,
            self.sriov_vfs_port[1][0].pci,
            self.sriov_vfs_port[2][0].pci,
            self.sriov_vfs_port[3][0].pci,
        ]
        VF_SCRIPT_FILE = "./examples/ip_pipeline/examples/l2fwd.cli"

        vf_eal_para = self.dut.create_eal_parameters(
            cores=list(range(2)), ports=DUT_VF_PORTS
        )
        vf_cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, vf_eal_para, VF_SCRIPT_FILE
        )
        self.session_secondary.send_expect(vf_cmd, "fwd port 2", 60)

        # rule 0 test
        pcap_file = "/tmp/pt_0.pcap"
        pkt = [
            Ether(dst=self.vf0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/pt_1.pcap"
        pkt = [
            Ether(dst=self.vf1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/pt_2.pcap"
        pkt = [
            Ether(dst=self.vf2_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(2, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/pt_3.pcap"
        pkt = [
            Ether(dst=self.vf3_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(3, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        self.destroy_env(self.port_nums, driver=self.drivername)
        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]["port"]
            port.bind_driver(driver=self.drivername)

    def test_pipeline_with_tap(self):
        """
        pipeline with tap
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/tap.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/tap.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = [self.dut_p0_pci, self.dut_p1_pci]
        SCRIPT_FILE = "./examples/ip_pipeline/examples/tap.cli"

        eal_para = self.dut.create_eal_parameters(cores=list(range(2)), ports=DUT_PORTS)
        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 3", 60)

        tap_session = self.dut.new_session()
        cmd = "ip link set br1 down; brctl delbr br1"
        tap_session.send_expect(cmd, "# ", 20)
        cmd = "brctl addbr br1; brctl addif br1 TAP0; brctl addif br1 TAP1"
        tap_session.send_expect(cmd, "# ", 20)
        cmd = "ifconfig TAP0 up;  ifconfig TAP1 up; ifconfig br1 up"
        tap_session.send_expect(cmd, "# ", 20)
        # rule 0 test
        pcap_file = "/tmp/tap_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "link 1 failed to receive packet")

        # rule 1 test
        pcap_file = "/tmp/tap_1.pcap"
        pkt = [
            Ether(dst=self.dut_p1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "tcp"
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "link 0 failed to receive packet")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

        cmd = "ip link set br1 down; brctl delbr br1"
        tap_session.send_expect(cmd, "# ", 20)
        self.dut.close_session(tap_session)

    def test_rss_pipeline(self):
        """
        rss pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = [self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci]
        SCRIPT_FILE = "./examples/ip_pipeline/examples/rss.cli"

        eal_para = self.dut.create_eal_parameters(cores=list(range(5)), ports=DUT_PORTS)
        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "PIPELINE3 enable", 60)

        # rule 0 test
        pcap_file = "/tmp/rss_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.10.1", dst="100.0.20.2")
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.0.20.2"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.0.20.2" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/rss_1.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.0", dst="100.0.0.1")
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.0.0.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.0.0.1" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/rss_2.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.10.1", dst="100.0.0.2")
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.0.0.2"
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.0.0.2" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/rss_3.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.1", dst="100.0.10.2")
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 100.0.10.2"
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.0.10.2" in dst_ip_list, "rule 3 test fail")

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
