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
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP, GRE, Dot1Q
from scapy.layers.sctp import SCTP, SCTPChunkData
from scapy.packet import Raw, bind_layers
from scapy.route import *
from scapy.sendrecv import sendp, sniff
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


class TestFlowClassifySoftnic(TestCase):

    def copy_config_files_to_dut(self):
        """
        Copy firmware.cli from tester to DUT.
        """
        file = 'flow_classify_softnic.tar.gz'
        src_file = r'./dep/%s' % file
        dst1 = '/tmp'
        dst2 = '/root/dpdk/drivers/net/softnic'
        self.dut.session.copy_file_to(src_file, dst1)
        self.dut.send_expect("tar xf %s/%s -C %s" % (dst1, file, dst2), "#", 30)

    def start_testpmd(self, filename, port_num):
        """
        Start testpmd.
        """
        self.cores = self.dut.get_core_list("all")
        self.set_ports(filename, port_num)
        TESTPMD = self.dut.apps_name['test-pmd']
        cmd="cat /sys/bus/pci/devices/%s/numa_node"%self.dut_p0_pci
        numa_node = int(self.dut.send_expect(cmd, "# ", 60))
        cpu_id = numa_node if numa_node > 0 else 0
        ports_info = []
        for i in range(port_num):
            ports_info.append(i)
        eal_params = self.dut.create_eal_parameters(cores=self.cores, ports=ports_info)
        VDEV = "--vdev 'net_softnic0,firmware=./drivers/net/softnic/flow_classify_softnic/%s,cpu_id=%s,conn_port=8086'" % (filename,cpu_id)
        if port_num == 4:
            cmd = "{0} {1} {2} -s 0x10 -- -i --rxq=4 --txq=4 --disable-rss --portmask=0x10".format(TESTPMD, VDEV, eal_params)
        elif port_num == 2:
            cmd = "{0} {1} {2} -s 0x4 -- -i --rxq=2 --txq=2 --disable-rss --portmask=0x4".format(TESTPMD, VDEV, eal_params)
        else:
            raise Exception("The number of port is wrong!")
        self.dut.send_expect(cmd, "testpmd> ", 60)

    def set_ports(self, filename, port_num):
        """
        Set actual ports.
        """
        self.dut.send_expect("sed -i '/^link LINK/d' ./drivers/net/softnic/flow_classify_softnic/%s" % filename, "# ", 20)
        cmd = "sed -i '1i\link LINK0 dev %s' ./drivers/net/softnic/flow_classify_softnic/%s" % (self.dut_p0_pci, filename)
        self.dut.send_expect(cmd, "# ", 20)
        cmd = "sed -i '2i\link LINK1 dev %s' ./drivers/net/softnic/flow_classify_softnic/%s" % (self.dut_p1_pci, filename)
        self.dut.send_expect(cmd, "# ", 20)
        if port_num == 4:
            cmd = "sed -i '3i\link LINK2 dev %s' ./drivers/net/softnic/flow_classify_softnic/%s" % (self.dut_p2_pci, filename)
            self.dut.send_expect(cmd, "# ", 20)
            cmd = "sed -i '4i\link LINK3 dev %s' ./drivers/net/softnic/flow_classify_softnic/%s" % (self.dut_p3_pci, filename)
            self.dut.send_expect(cmd, "# ", 20)
        self.dut.send_expect("sed -i 's/^thread 4 pipeline/thread %d pipeline/g' ./drivers/net/softnic/flow_classify_softnic/%s" % (self.port_num, filename), "# ", 20)

    def set_table(self, cmd, filename):
        """
        Set pipeline table.
        """
        self.dut.send_expect("sed -i '/^pipeline RX table match/d' ./drivers/net/softnic/flow_classify_softnic/%s" % filename, "# ", 20)
        command = "sed -i \'/^table action/a" + cmd + "\' ./drivers/net/softnic/flow_classify_softnic/%s" % filename
        self.dut.send_expect(command, "# ", 20)

    def get_flow_direction_param_of_tcpdump(self):
        """
        get flow dirction param depend on tcpdump version
        """
        param = ""
        direct_param = r"(\s+)\[ (\S+) in\|out\|inout \]"
        out = self.tester.send_expect('tcpdump -h', '# ', trim_whitespace=False)
        for line in out.split('\n'):
            m = re.match(direct_param, line)
            if m:
                opt = re.search("-Q", m.group(2));
                if opt:
                    param = "-Q" + " in"
                else:
                    opt = re.search("-P", m.group(2));
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
        command = 'tcpdump -n -e {0} -w /tmp/tcpdump_{1}.pcap -i {1} {2} 2>/tmp/tcpdump_{1}.out &'\
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
        sleep(3)

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
        self.pmdout.wait_link_status_up('all')
        tx_port = self.tester.get_local_port(self.dut_ports[from_port%self.port_num])
        rx_port = self.tester.get_local_port(self.dut_ports[to_port%self.port_num])

        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)
        # check tester's link status before send packet
        for iface in [tx_interface, rx_interface]:
            self.verify(self.tester.is_interface_up(intf=iface), "Wrong link status, should be up")

        self.tcpdump_start_sniff(rx_interface, filters)

        # Prepare the pkts to be sent
        self.tester.scapy_foreground()
        self.tester.scapy_append('pkt = rdpcap("%s")' % (pcap_file))
        self.tester.scapy_append('sendp(pkt, iface="%s", count=%d)' % (tx_interface, count))
        self.tester.scapy_execute()

        self.tcpdump_stop_sniff()

        return self.read_pcap_file('/tmp/tcpdump_%s.pcap' % rx_interface)

    def send_pkts(self, from_port, pcap_file, count=1):
        """
        Sent pkts that read from the pcap_file.
        """
        tx_port = self.tester.get_local_port(self.dut_ports[from_port])
        tx_interface = self.tester.get_interface(tx_port)

        # Prepare the pkts to be sent
        self.tester.scapy_foreground()
        self.tester.scapy_append('pkt = rdpcap("%s")' % (pcap_file))
        self.tester.scapy_append('sendp(pkt, iface="%s", count=%d)' % (tx_interface, count))
        self.tester.scapy_execute()

    def send_and_check_packets(self, pcap_file, pkt, ltype, src_dst, addr_port, from_port, to_port):
        """
        Sent pkts that read from the pcap_file.
        Check if the rule works.
        """
        self.write_pcap_file(pcap_file, pkt)
        checklist = []
        if ltype in ["udp", "tcp", "sctp"]:
            filters = "%s %s port %d" % (ltype, src_dst, addr_port)
            sniff_pkts = self.send_and_sniff_pkts(from_port, to_port, pcap_file, filters)
            for packet in sniff_pkts:
                if src_dst == "src":
                    checklist.append(packet.getlayer(2).sport)
                elif src_dst == "dst":
                    checklist.append(packet.getlayer(2).dport)
        elif ltype in ["ipv4", "ipv6"]:
            filters = "%s host %s" % (src_dst, addr_port)
            sniff_pkts = self.send_and_sniff_pkts(from_port, to_port, pcap_file, filters)

            for packet in sniff_pkts:
                if src_dst == "src":
                    checklist.append(packet.getlayer(1).src)
                elif src_dst == "dst":
                    checklist.append(packet.getlayer(1).dst)
            addr_port = str.lower(addr_port)
        self.verify(addr_port in checklist, "rule test fail")

    def check_status(self, rx_pkt_num, tx_pkt_num, port):
        """
        Check port status
        """
        rx_num = 0
        tx_num = 0
        for i in range(port):
            stats = self.pmdout.get_pmd_stats(self.dut_ports[i])
            rx_num = rx_num + stats['RX-packets']
            tx_num = tx_num + stats['TX-packets']
        self.verify((rx_num == rx_pkt_num) and (tx_num == tx_pkt_num), "The rule failed to work")

    def generate_rules(self, operation="create", port=4, group=0, iptype="ipv4", src_mask="0.0.0.0", dst_mask="0.0.0.0", src_spec="0.0.0.0", dst_spec="0.0.0.0", protomask=0, protospec=17, l4type="udp", sportmask=0, dportmask=0, sportspec=0, dportspec=0, action="queue", index=[]):
        """
        Generate flow rules
        """
        if port == 4:
            port = self.port_num
        if iptype == "ipv6":
            if src_mask == "0.0.0.0":
                src_mask = "0:0:0:0:0:0:0:0"
            if dst_mask == "0.0.0.0":
                dst_mask = "0:0:0:0:0:0:0:0"
            if src_spec == "0.0.0.0":
                src_spec = "0:0:0:0:0:0:0:0"
            if dst_spec == "0.0.0.0":
                dst_spec = "0:0:0:0:0:0:0:0"
        if action == "queue":
            actions = "queue index %d" % (index[0]%port)
        elif action == "jump":
            actions = "jump group %d" % (index[0]%port)
        elif action == "rss":
            queue_idx = ""
            for queue in index:
                queue_idx = queue_idx + str(queue%port) + " "
            actions = "rss queues %s end" % queue_idx

        if l4type == "":
            self.dut.send_expect("flow %s %d group %d ingress pattern eth / %s proto mask %d src mask %s dst mask %s src spec %s dst spec %s / end actions %s / end" % (operation, port, group, iptype, protomask, src_mask, dst_mask, src_spec, dst_spec, actions), operation, 60)
        else:
            self.dut.send_expect("flow %s %d group %d ingress pattern eth / %s proto mask %d src mask %s dst mask %s src spec %s dst spec %s proto spec %d / %s src mask %d dst mask %d src spec %d dst spec %d / end actions %s / end" % (operation, port, group, iptype, protomask, src_mask, dst_mask, src_spec, dst_spec, protospec, l4type, sportmask, dportmask, sportspec, dportspec, actions), operation, 60)

    def send_continuous_packet(self, ptype, src_dst, src_addr, dst_addr, itf):
        """
        Sends continuous packets.
        """
        self.pmdout.wait_link_status_up('all')
        self.verify(self.tester.is_interface_up(intf=itf), "Wrong link status, should be up")
        self.tester.scapy_foreground()
        if src_dst == "src":
            if ptype == "ipv4":
                var = src_addr.split(".")
                string = "."
                ipaddr = string.join(var[0:3])
                for i in range(32):
                    packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="%s.%d", dst="%s", proto=17)/UDP(sport=100, dport=200)], iface="%s")' % (
                        self.dut_p0_mac, itf, ipaddr, i, dst_addr, itf)
                    self.tester.scapy_append(packet)
                self.tester.scapy_execute()
            elif ptype == "ipv6":
                var = src_addr.split(":")
                string = ":"
                if len(var) == 8:
                    ipaddr = string.join(var[0:7])
                else:
                    ipaddr = string.join(var[0:(len(var) - 1)])
                for i in range(16):
                    packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="%s:%d", dst="%s", nh=17)/UDP(sport=100, dport=200)], iface="%s")' % (
                        self.dut_p0_mac, itf, ipaddr, i, dst_addr, itf)
                    self.tester.scapy_append(packet)
                self.tester.scapy_execute()

        elif src_dst == "dst":
            if ptype == "ipv4":
                var = dst_addr.split(".")
                string = "."
                ipaddr = string.join(var[0:3])
                for i in range(32):
                    packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="%s", dst="%s.%d", proto=17)/UDP(sport=100, dport=100)], iface="%s")' % (
                        self.dut_p0_mac, itf, src_addr, ipaddr, i, itf)
                    self.tester.scapy_append(packet)
                self.tester.scapy_execute()
            elif ptype == "ipv6":
                var = dst_addr.split(":")
                string = ":"
                if len(var) == 8:
                    ipaddr = string.join(var[0:7])
                else:
                    ipaddr = string.join(var[0:(len(var) - 1)])
                for i in range(16):
                    packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="%s", dst="%s:%d", nh=17)/UDP(sport=100, dport=200)], iface="%s")' % (
                        self.dut_p0_mac, itf, src_addr, ipaddr, i, itf)
                    self.tester.scapy_append(packet)
                self.tester.scapy_execute()

    def check_packet_queue(self, queues=[], out=""):
        """
        Get the queue which packet enter.
        """
        time.sleep(2)
        for queue in queues:
            self.verify("Queue= %d" % (queue%self.port_num) in out, "There is some queues doesn't work.")
        lines = out.split("\r\n")
        reta_line = {}
        queue_flag = 0
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if queue_flag == 1:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                rxpkt_num = m.group(1)
                result_scanner = r"TX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                txpkt_num = m.group(1)
                self.verify(rxpkt_num == txpkt_num, "There are some packets failed to forward.")
                queue_flag = 0
            elif line.strip().startswith("------- Forward"):
                queue_flag = 1

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.port_num = len(self.dut_ports)
        self.verify(self.port_num == 2 or self.port_num == 4,
                    "Insufficient ports for speed testing")

        self.dut_p0_pci = self.dut.get_port_pci(self.dut_ports[0])
        self.dut_p1_pci = self.dut.get_port_pci(self.dut_ports[1])
        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.dut_p1_mac = self.dut.get_mac_address(self.dut_ports[1])
        self.pf0_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf1_interface = self.dut.ports_info[self.dut_ports[1]]['intf']

        if self.port_num == 4:
            self.dut_p2_pci = self.dut.get_port_pci(self.dut_ports[2])
            self.dut_p3_pci = self.dut.get_port_pci(self.dut_ports[3])
            self.dut_p2_mac = self.dut.get_mac_address(self.dut_ports[2])
            self.dut_p3_mac = self.dut.get_mac_address(self.dut_ports[3])
            self.pf2_interface = self.dut.ports_info[self.dut_ports[2]]['intf']
            self.pf3_interface = self.dut.ports_info[self.dut_ports[3]]['intf']

        self.ipv4_mask = "255.255.255.255"
        self.ipv6_mask = "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
        self.portmask = 65535
        self.protomask = 255

        self.pmdout = PmdOutput(self.dut)
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.copy_config_files_to_dut()

        self.param_flow_dir = self.get_flow_direction_param_of_tcpdump()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_ipv4_acl_table(self):
        """
        Ipv4 ACL table
        """
        filename = "flow_ipv4_acl_firmware.cli"
        self.start_testpmd(filename, self.port_num)

        # validate rule
        self.generate_rules(operation="validate", dst_mask="255.192.0.0", dst_spec="2.0.0.0", sportspec=100, dportspec=200, index=[3])

        # create rule
        self.generate_rules(dst_mask="255.192.0.0", dst_spec="2.0.0.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[3])
        self.generate_rules(dst_mask="255.192.0.0", dst_spec="2.64.0.0", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[2])
        self.generate_rules(src_mask="255.192.0.0", src_spec="2.128.0.0", protomask=self.protomask, protospec=132, l4type="sctp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(dst_mask="255.192.0.0", dst_spec="4.0.0.0", protomask=self.protomask, sportspec=100, sportmask=self.portmask, dportmask=self.portmask, dportspec=200, index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='2.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.0.0.0", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='2.64.0.0', proto=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.64.0.0", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='2.128.0.0', dst='0.0.0.0', proto=132)/SCTP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "src", "2.128.0.0", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='4.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "4.0.0.0", 0, 0)

        # send another 3 packets
        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='3.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='2.64.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='2.128.0.0', dst='0.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(7, 4, self.port_num)

        # query rule
        out = self.dut.send_expect("flow query %d 3 queue" % self.port_num, "QUEUE", 60)

        # destroy rule 1
        self.dut.send_expect("flow destroy %d rule 1" % self.port_num, "Flow rule #1 destroyed", 60)
        destroy_out = self.dut.send_expect("flow list %d" % self.port_num, "testpmd> ", 60)
        self.verify("1" not in destroy_out, "destroy rule fail")

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='2.64.0.0', proto=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 2.64.0.0"
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("2.64.0.0" not in dst_ip_list, "rule 1 test fail")

        # flush rules
        self.dut.send_expect("flow flush %d" % self.port_num, "testpmd> ", 60)
        flush_out = self.dut.send_expect("flow list %d" % self.port_num, "testpmd> ", 60)
        self.verify("Rule" not in flush_out, "flush rule fail")
        self.dut.send_expect("clear port stats all", "testpmd> ", 60)

        # test all the rules
        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='2.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='2.64.0.0', proto=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='2.128.0.0', dst='0.0.0.0', proto=132)/SCTP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='4.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(4, 0, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_5tuple_hash_table(self):
        """
        Ipv4 5tuple hash table
        """
        filename = "flow_ipv4_5tuple_hash_firmware.cli"
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.1", dst_spec="200.0.0.1", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=101, dportspec=201, index=[3])
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.2", dst_spec="200.0.0.2", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=102, dportspec=202, index=[2])
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.3", dst_spec="200.0.0.3", protomask=self.protomask, protospec=132, l4type="sctp", sportmask=self.portmask, dportmask=self.portmask, sportspec=103, dportspec=203, index=[1])
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.4", dst_spec="200.0.0.4", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=104, dportspec=204, index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.1', dst='200.0.0.1', proto=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.1", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.2', dst='200.0.0.2', proto=17)/UDP(sport=102, dport=202)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.2", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.3', dst='200.0.0.3', proto=132)/SCTP(sport=103, dport=203)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.3", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.4', dst='200.0.0.4', proto=17)/UDP(sport=104, dport=204)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.4", 0, 0)

        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_addr_hash_table(self):
        """
        Ipv4 addr hash table
        """
        filename = "flow_ipv4_addr_hash_firmware.cli"

        # match ipv4 src_addr
        cmd = "pipeline RX table match hash ext key 8 mask FFFFFFFF00000000 offset 282 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(src_mask=self.ipv4_mask, src_spec="100.0.0.1", dst_spec="200.0.0.1", sportspec=100, dportspec=200, index=[3])
        self.generate_rules(src_mask=self.ipv4_mask, src_spec="100.0.0.2", dst_spec="200.0.0.1", sportspec=100, dportspec=200, index=[2])
        self.generate_rules(src_mask=self.ipv4_mask, src_spec="100.0.0.3", dst_spec="200.0.0.1", sportspec=100, dportspec=200, index=[1])
        self.generate_rules(src_mask=self.ipv4_mask, src_spec="100.0.0.4", dst_spec="200.0.0.1", sportspec=100, dportspec=200, index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.1', dst='200.0.0.1', proto=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "src", "100.0.0.1", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.2', dst='200.0.0.2', proto=17)/UDP(sport=102, dport=202)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "src", "100.0.0.2", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.3', dst='200.0.0.3', proto=132)/SCTP(sport=103, dport=203)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "src", "100.0.0.3", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.4', dst='200.0.0.4')/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "src", "100.0.0.4", 0, 0)
        self.dut.send_expect("quit", "# ", 60)

        # match ipv4 dst_addr
        cmd = "pipeline RX table match hash ext key 8 mask FFFFFF0000000000 offset 286 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(dst_mask="255.255.255.0", src_spec="100.0.0.1", dst_spec="200.0.0.1", sportspec=100, dportspec=200, index=[3])
        self.generate_rules(dst_mask="255.255.255.0", src_spec="100.0.0.1", dst_spec="200.0.1.1", protospec=6, l4type="tcp", sportspec=100, dportspec=200, index=[2])
        self.generate_rules(dst_mask="255.255.255.0", src_spec="100.0.0.1", dst_spec="200.0.2.1", protospec=132, l4type="sctp", sportspec=100, dportspec=200, index=[1])
        self.generate_rules(dst_mask="255.255.255.0", src_spec="100.0.0.1", dst_spec="200.0.3.1", l4type="", index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.1', dst='200.0.0.1', proto=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.1", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.2', dst='200.0.1.2', proto=17)/UDP(sport=102, dport=202)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.1.2", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.3', dst='200.0.2.3', proto=132)/SCTP(sport=103, dport=203)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.2.3", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.4', dst='200.0.3.4')/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.3.4", 0, 0)
        self.dut.send_expect("quit", "# ", 60)

        # match sport
        cmd = "pipeline RX table match hash ext key 8 mask FFFF000000000000 offset 290 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(src_spec="100.0.0.1", dst_spec="200.0.0.1", sportmask=self.portmask, sportspec=100, dportspec=200, index=[3])
        self.generate_rules(src_spec="100.0.0.1", dst_spec="200.0.0.1", protospec=6, l4type="tcp", sportmask=self.portmask, sportspec=101, dportspec=200, index=[2])
        self.generate_rules(src_spec="100.0.0.1", dst_spec="200.0.0.1", protospec=132, l4type="sctp", sportmask=self.portmask, sportspec=102, dportspec=200, index=[1])
        self.generate_rules(src_spec="100.0.0.1", dst_spec="200.0.0.1", sportmask=self.portmask, sportspec=103, dportspec=200, index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.1', dst='200.0.0.1', proto=6)/TCP(sport=100, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "tcp", "src", 100, 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.2', dst='200.0.1.2', proto=17)/UDP(sport=101, dport=202)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "udp", "src", 101, 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.3', dst='200.0.2.3', proto=132)/SCTP(sport=102, dport=203)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "sctp", "src", 102, 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.2', dst='200.0.1.2', proto=17)/UDP(sport=103, dport=202)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "udp", "src", 103, 0, 0)

        # send a packet without l4 info
        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.4', dst='200.0.3.4')/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)
        self.check_status(5, 4, self.port_num)

        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_acl_table(self):
        """
        Ipv6 acl table
        """
        filename = "flow_ipv6_acl_firmware.cli"
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", protomask=self.protomask, index=[3])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", protomask=self.protomask, protospec=6, l4type="tcp", index=[2])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", protomask=self.protomask, protospec=132, l4type="sctp", index=[1])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", protomask=self.protomask, sportmask=self.portmask, sportspec=100, index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:5789', dst='2001::2', nh=17)/UDP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:6789', dst='2001::2', nh=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:7789', dst='2001::2', nh=132)/SCTP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:8789', dst='2001::2', nh=17)/UDP(sport=100, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "udp", "src", 100, 0, 0)

        # send another 3 packets
        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:9789', dst='2001::2', nh=17)/UDP(sport=101, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:8789', dst='2001::2', nh=17)/UDP(sport=101, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:6789', dst='2001::2', nh=17)/TCP(sport=101, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(7, 4, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_addr_hash_table(self):
        """
        Ipv6 addr hash table
        """
        filename = "flow_ipv6_addr_hash_firmware.cli"

        # match ipv6 src_addr
        cmd = "pipeline RX table match hash ext key 16 mask FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", index=[3])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", index=[2])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", index=[1])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:5789', dst='2001::2', nh=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:6789', dst='2001::2', nh=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:7789', dst='2001::2', nh=132)/SCTP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:8789', dst='2001::2', nh=17)/UDP(sport=100, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", 0, 0)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='ABCD:EF01:2345:6789:ABCD:EF01:2345:9789', dst='2001::2', nh=17)/UDP(sport=101, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)
        self.check_status(5, 4, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

        # match ipv6 dst_addr
        cmd = "pipeline RX table match hash ext key 16 mask FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF offset 294 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", dst_mask=self.ipv6_mask, dst_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", index=[3])
        self.generate_rules(iptype="ipv6", dst_mask=self.ipv6_mask, dst_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", index=[2])
        self.generate_rules(iptype="ipv6", dst_mask=self.ipv6_mask, dst_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", index=[1])
        self.generate_rules(iptype="ipv6", dst_mask=self.ipv6_mask, dst_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(dst='ABCD:EF01:2345:6789:ABCD:EF01:2345:5789', src='2001::2', nh=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "ABCD:EF01:2345:6789:ABCD:EF01:2345:5789", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(dst='ABCD:EF01:2345:6789:ABCD:EF01:2345:6789', src='2001::2', nh=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "ABCD:EF01:2345:6789:ABCD:EF01:2345:6789", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(dst='ABCD:EF01:2345:6789:ABCD:EF01:2345:7789', src='2001::2', nh=132)/SCTP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "ABCD:EF01:2345:6789:ABCD:EF01:2345:7789", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(dst='ABCD:EF01:2345:6789:ABCD:EF01:2345:8789', src='2001::2', nh=17)/UDP(sport=100, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "ABCD:EF01:2345:6789:ABCD:EF01:2345:8789", 0, 0)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(dst='ABCD:EF01:2345:6789:ABCD:EF01:2345:9789', src='2001::2', nh=17)/UDP(sport=101, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)
        self.check_status(5, 4, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_5tuple_hash_table(self):
        """
        Ipv6 5tuple hash table
        """
        filename = "flow_ipv6_5tuple_hash_firmware.cli"
        cmd = "pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::1", dst_spec="0::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=101, dportspec=201, index=[3])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::2", dst_spec="0::2", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=102, dportspec=202, index=[2])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::3", dst_spec="0::3", protomask=self.protomask, protospec=132, l4type="sctp", sportmask=self.portmask, dportmask=self.portmask, sportspec=103, dportspec=203, index=[1])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::4", dst_spec="0::4", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=104, dportspec=204, index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="2001::1", dst="0::1", nh=17)/UDP(sport=101, dport=201)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "2001::1", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::2', dst='0::2', nh=6)/TCP(sport=102, dport=202)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "2001::2", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::3', dst='0::3', nh=132)/SCTP(sport=103, dport=203)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "2001::3", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::4', dst='0::4', nh=17)/UDP(sport=104, dport=204)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "src", "2001::4", 0, 0)

        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="2001::1", dst="0::1", nh=6)/TCP(sport=101, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)
        self.check_status(5, 4, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_inconsistent_rules(self):
        """
        Flow rule item is inconsistent with table match format
        """
        # ipv4
        filename = "flow_ipv4_addr_hash_firmware.cli"
        cmd = "pipeline RX table match hash ext key 8 mask FFFFFFFF00000000 offset 282 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.dut.send_expect("flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 dst mask 255.255.255.255 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end", "error", 60)
        self.dut.send_expect("quit", "# ", 60)

        cmd = "pipeline RX table match hash ext key 8 mask FFFFFF0000000000 offset 286 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)
        self.dut.send_expect("flow create 4 group 0 ingress pattern eth / ipv4 proto mask 0 src mask 0.0.0.0 dst mask 255.255.255.255 src spec 100.0.0.1 dst spec 200.0.0.1 proto spec 17 / udp src mask 0 dst mask 0 src spec 100 dst spec 200 / end actions queue index 3 / end", "error", 60)
        self.dut.send_expect("quit", "# ", 60)

        # ipv6
        filename = "flow_ipv6_5tuple_hash_firmware.cli"
        cmd = "pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)
        self.dut.send_expect("flow create 4 group 0 ingress pattern eth / ipv6 proto mask 255 src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff src spec 2001::1 dst spec 0::1 proto spec 17 / udp src mask 0 dst mask 65535 src spec 31 dst spec 41 / end actions queue index 3 / end", "error", 60)
        self.dut.send_expect("quit", "# ", 60)

        cmd = "pipeline RX table match hash ext key 16 mask FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF offset 294 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)
        self.dut.send_expect("flow create 4 group 0 ingress pattern eth / ipv6 proto mask 0  src mask ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff dst mask 0:0:0:0:0:0:0:0 src spec ABCD:EF01:2345:6789:ABCD:EF01:2345:5789 dst spec 0:0:0:0:0:0:0:0 proto spec 17 / udp src mask 0 dst mask 0 src spec 0 dst spec 0 / end actions queue index 3 / end", "error", 60)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_hash_rss_action(self):
        """
        Set rss action using acl table.
        """
        filename = "flow_ipv4_rss_firmware.cli"

        # match ipv4 src_addr
        cmd = "pipeline RX table match hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.1", dst_spec="200.0.0.1", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[3])
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.2", dst_spec="200.0.0.2", protomask=self.protomask, protospec=17, l4type="udp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[2])
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.3", dst_spec="200.0.0.3", protomask=self.protomask, protospec=132, l4type="sctp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[1])
        self.generate_rules(src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="100.0.0.4", dst_spec="200.0.0.4", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.1', dst='200.0.0.1', proto=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.1", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.2', dst='200.0.0.2', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.2", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.3', dst='200.0.0.3', proto=132)/SCTP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "src", "100.0.0.3", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.4', dst='200.0.0.4', proto=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.4", 0, 0)

        # not match test
        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='100.0.0.4', dst='200.0.0.4', proto=6)/TCP(sport=101, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)
        self.check_status(5, 4, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

        # match ipv4 src_addr
        cmd = "pipeline RX table match hash ext key 16 mask 00FF0000FFFFFF00FFFFFFFFFFFFFFFF offset 278 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        self.generate_rules(src_mask="255.255.255.0", dst_mask=self.ipv4_mask, src_spec="100.0.0.1", dst_spec="200.0.0.1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0, 1, 2, 3])
        self.generate_rules(src_mask="255.255.255.0", dst_mask=self.ipv4_mask, src_spec="100.0.1.2", dst_spec="200.0.0.1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0, 1, 2, 3])
        self.dut.send_expect("start", "testpmd> ", 60)

        self.send_continuous_packet("ipv4", "src", "100.0.0.1", "200.0.0.1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([0, 1, 2, 3], out)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.send_continuous_packet("ipv4", "src", "100.0.1.2", "200.0.0.1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([0, 1, 2, 3], out)
        self.dut.send_expect("quit", "# ", 60)

        # match ipv4 src_addr
        cmd = "pipeline RX table match hash ext key 8 mask FFFF0000FFFFFFFF offset 282 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        self.generate_rules(src_mask="255.255.0.0", dst_mask=self.ipv4_mask, src_spec="100.0.0.1", dst_spec="200.0.0.1", sportspec=100, dportspec=200, action="rss", index=[0])
        self.generate_rules(src_mask="255.255.0.0", dst_mask=self.ipv4_mask, src_spec="100.0.0.1", dst_spec="200.0.0.2", sportspec=100, dportspec=200, action="rss", index=[2, 3])
        self.generate_rules(src_mask="255.255.0.0", dst_mask=self.ipv4_mask, src_spec="200.0.0.1", dst_spec="200.0.0.2", sportspec=100, dportspec=200, action="rss", index=[1, 2])
        self.dut.send_expect("start", "testpmd> ", 60)

        self.send_continuous_packet("ipv4", "src", "100.0.0.1", "200.0.0.1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([0], out)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.send_continuous_packet("ipv4", "src", "100.0.1.1", "200.0.0.2", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([2, 3], out)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.send_continuous_packet("ipv4", "src", "200.0.0.1", "200.0.0.2", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([1, 2], out)

        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_hash_rss_action(self):
        """
        Set rss action using hash table.
        """
        filename = "flow_ipv6_rss_firmware.cli"

        # match ipv6 src_addr
        cmd = "pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::1", dst_spec="1001::1", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[3])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::2", dst_spec="1001::2", protomask=self.protomask, protospec=17, l4type="udp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[2])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::3", dst_spec="1001::3", protomask=self.protomask, protospec=132, l4type="sctp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[1])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="2001::4", dst_spec="1001::4", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::1', dst='1001::1', nh=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "1001::1", 0, 3)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::2', dst='1001::2', nh=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "1001::2", 0, 2)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::3', dst='1001::3', nh=132)/SCTP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "1001::3", 0, 1)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::4', dst='1001::4', nh=6)/TCP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "1001::4", 0, 0)

        # not match test
        pcap_file = '/tmp/route_4.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src='2001::1', dst='1001::1', nh=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)
        self.check_status(5, 4, self.port_num)
        self.dut.send_expect("quit", "# ", 60)

        cmd = "pipeline RX table match hash ext key 64 mask 0000FF00FFFFFFFFFFFFFFFFFFFFFFFFFFFF0000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", src_mask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:0", dst_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2345:0", dst_spec="0::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0, 1, 2, 3])
        self.generate_rules(iptype="ipv6", src_mask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:0", dst_mask=self.ipv6_mask, src_spec="ABCD:EF01:2345:6789:ABCD:EF01:2346:0", dst_spec="0::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0, 1, 2, 3])
        self.dut.send_expect("start", "testpmd> ", 60)

        self.send_continuous_packet("ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2345:0", "0::1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([0, 1, 2, 3], out)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.send_continuous_packet("ipv6", "src", "ABCD:EF01:2345:6789:ABCD:EF01:2346:0", "0::1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([0, 1, 2, 3], out)
        self.dut.send_expect("quit", "# ", 60)

        cmd = "pipeline RX table match hash ext key 64 mask 00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0000FFFFFFFF000000000000000000000000000000000000000000000000 offset 274 buckets 16K size 64K action AP0"
        self.set_table(cmd, filename)
        self.start_testpmd(filename, self.port_num)

        # create rule
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:0", src_spec="2001::1", dst_spec="1001::1", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[0])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:0", src_spec="2001::2", dst_spec="1001::1", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[2, 3])
        self.generate_rules(iptype="ipv6", src_mask=self.ipv6_mask, dst_mask="ffff:ffff:ffff:ffff:ffff:ffff:ffff:0", src_spec="2001::1", dst_spec="1002::1", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="rss", index=[1, 2])
        self.dut.send_expect("start", "testpmd> ", 60)

        self.send_continuous_packet("ipv6", "dst", "2001::1", "1001::1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([0], out)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.send_continuous_packet("ipv6", "dst", "2001::2", "1001::1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([2, 3], out)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.send_continuous_packet("ipv6", "dst", "2001::1", "1002::1", self.tester_itf)
        out = self.dut.send_expect("stop", "testpmd> ", 120)
        self.check_packet_queue([1, 2], out)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_acl_jump(self):
        """
        Set jump action using acl table.
        """
        filename = "flow_ipv4_acl_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, dst_mask="255.192.0.0", dst_spec="200.0.0.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, dst_mask="255.192.0.0", dst_spec="200.64.0.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, dst_mask="255.192.0.0", dst_spec="200.0.0.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, dst_mask="255.192.0.0", dst_spec="200.64.0.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='200.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.0.0.0", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='200.64.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "200.64.0.0", 0, 1)

        # destroy rules of group 1
        self.dut.send_expect("flow destroy 2 rule 0", "testpmd> ", 60)
        self.dut.send_expect("flow destroy 2 rule 1", "testpmd> ", 60)
        destroy_out = self.dut.send_expect("flow list 2", "testpmd> ", 60)
        self.verify("QUEUE" not in destroy_out, "destroy rule fail")

        # rule 2 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='0.0.0.0', dst='200.0.0.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 200.0.0.0"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.0" not in dst_ip_list, "rule 2 test fail")

        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_hash_jump(self):
        """
        Set jump action using hash table.
        """
        filename = "flow_ipv4_hash_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.0", dst_spec="2.20.21.0", protomask=self.protomask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.1", dst_spec="2.20.21.1", protomask=self.protomask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.0", dst_spec="2.20.21.0", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.1", dst_spec="2.20.21.1", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.0', dst='2.20.21.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.20.21.0", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.1', dst='2.20.21.1', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.20.21.1", 0, 1)

        # destroy rules of group 1
        self.dut.send_expect("flow destroy 2 rule 0", "Flow rule #0 destroyed", 60)
        self.dut.send_expect("flow destroy 2 rule 1", "Flow rule #1 destroyed", 60)
        destroy_out = self.dut.send_expect("flow list 2", "testpmd> ", 60)
        self.verify("QUEUE" not in destroy_out, "destroy rule fail")

        # rule 2 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.1', dst='2.20.21.1', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 2.20.21.1"
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("2.20.21.1" not in dst_ip_list, "rule 3 test fail")

        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_acl_hash_jump(self):
        """
        Set jump action from acl table to hash table.
        """
        filename = "flow_ipv4_acl_hash_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.0", dst_spec="2.20.21.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.1", dst_spec="2.20.21.1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.0", dst_spec="2.20.21.0", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.1", dst_spec="2.20.21.1", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.0', dst='2.20.21.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.20.21.0", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.1', dst='2.20.21.1', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.20.21.1", 0, 1)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.0', dst='2.20.21.0', proto=17)/UDP(sport=101, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.1', dst='2.20.21.1', proto=17)/UDP(sport=100, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(4, 2, port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv4_hash_acl_jump(self):
        """
        Set jump action from hash table to acl table.
        """
        filename = "flow_ipv4_hash_acl_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.0", dst_spec="2.20.21.0", protomask=self.protomask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, src_mask=self.ipv4_mask, dst_mask=self.ipv4_mask, src_spec="1.10.11.1", dst_spec="2.20.21.1", protomask=self.protomask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, src_mask=self.ipv4_mask, dst_mask="255.255.255.0", src_spec="1.10.11.0", dst_spec="2.20.21.0", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, src_mask=self.ipv4_mask, dst_mask="255.255.255.0", src_spec="1.10.11.1", dst_spec="2.20.21.1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.0', dst='2.20.21.0', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.20.21.0", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.1', dst='2.20.21.1', proto=17)/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv4", "dst", "2.20.21.1", 0, 1)

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.0', dst='2.20.21.2', proto=17)/UDP(sport=101, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        # rule 3 test
        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IP(src='1.10.11.1', dst='2.20.21.3', proto=17)/UDP(sport=100, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(4, 2, port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_acl_jump(self):
        """
        Set jump action with ipv6 acl table.
        """
        filename = "flow_ipv6_acl_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, iptype="ipv6", dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::2", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::2", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::1", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::2")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::2", 0, 1)

        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::2", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::1", 0, 0)

        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::2", dst="2001::2")/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(4, 3, port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_hash_jump(self):
        """
        Set jump action with ipv6 hash table.
        """
        filename = "flow_ipv6_hash_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::2", dst_spec="2001::2", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::2", dst_spec="2001::2", protomask=self.protomask, protospec=6, l4type="tcp", sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::1", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::2", dst="2001::2")/TCP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::2", 0, 1)

        # destroy rules of group 1
        self.dut.send_expect("flow destroy 2 rule 0", "Flow rule #0 destroyed", 60)
        self.dut.send_expect("flow destroy 2 rule 1", "Flow rule #1 destroyed", 60)
        destroy_out = self.dut.send_expect("flow list 2", "testpmd> ", 60)
        self.verify("QUEUE" not in destroy_out, "destroy rule fail")

        # rule 2 test
        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        filters = "dst host 2001::1"
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("2001::1" not in dst_ip_list, "rule 2 test fail")

        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_acl_hash_jump(self):
        """
        Set jump action from ipv6 acl table to hash table.
        """
        filename = "flow_ipv6_acl_hash_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::2", dst_spec="2001::2", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", dst_mask=self.ipv6_mask, src_spec="1001::2", dst_spec="2001::2", protomask=self.protomask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::1", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::2", dst="2001::2")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::2", 0, 1)

        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::3", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::4", dst="2001::2")/UDP(sport=100, dport=200)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(4, 2, port_num)
        self.dut.send_expect("quit", "# ", 60)

    def test_ipv6_hash_acl_jump(self):
        """
        Set jump action from ipv6 hash table to acl table.
        """
        filename = "flow_ipv6_hash_acl_jump_firmware.cli"
        port_num = 2
        self.start_testpmd(filename, port_num)

        # create rule
        self.generate_rules(port=port_num, group=1, iptype="ipv6", dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportmask=self.portmask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[0])
        self.generate_rules(port=port_num, group=1, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::2", dst_spec="2001::2", protomask=self.protomask, dportmask=self.portmask, sportspec=100, dportspec=200, index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::1", dst_spec="2001::1", protomask=self.protomask, sportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.generate_rules(port=port_num, iptype="ipv6", src_mask=self.ipv6_mask, dst_mask=self.ipv6_mask, src_spec="1001::2", dst_spec="2001::2", protomask=self.protomask, sportmask=self.portmask, sportspec=100, dportspec=200, action="jump", index=[1])
        self.dut.send_expect("start", "testpmd> ", 60)

        # rule 0 test
        pcap_file = '/tmp/route_0.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::1")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::1", 0, 0)

        # rule 1 test
        pcap_file = '/tmp/route_1.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::2", dst="2001::2")/UDP(sport=100, dport=200)/('X'*48)]
        self.send_and_check_packets(pcap_file, pkt, "ipv6", "dst", "2001::2", 0, 1)

        pcap_file = '/tmp/route_2.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::1", dst="2001::1")/UDP(sport=100, dport=201)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        pcap_file = '/tmp/route_3.pcap'
        pkt = [Ether(dst=self.dut_p0_mac)/IPv6(src="1001::2", dst="2001::2")/UDP(sport=100, dport=202)/('X'*48)]
        self.write_pcap_file(pcap_file, pkt)
        self.send_pkts(0, pcap_file)

        self.check_status(4, 2, port_num)
        self.dut.send_expect("quit", "# ", 60)

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
