# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

Tests for TSO.

"""
import os
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase

DEFAULT_MUT = 1500
TSO_MTU = 9000

class TestTSO(TestCase):
    dut_ports = []

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)

        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")

        # Verify that enough threads are available
        self.all_cores_mask = utils.create_mask(self.dut.get_core_list("all"))
        self.portMask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.loading_sizes = [128, 800, 801, 1700, 2500]
        self.rxfreet_values = [0, 8, 16, 32, 64, 128]

        self.test_cycles = [{'cores': '1S/1C/2T', 'Mpps': {}, 'pct': {}}]

        self.table_header = ['Frame Size']
        for test_cycle in self.test_cycles:
            self.table_header.append("%s Mpps" % test_cycle['cores'])
            self.table_header.append("% linerate")

        self.eal_param = self.dut.create_eal_parameters(cores='1S/1C/2T', socket=self.ports_socket, ports=self.dut_ports)

        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE[
            'ip'] + HEADER_SIZE['tcp']
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0])), TSO_MTU), "# ")
        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(
                                os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.path=self.dut.apps_name['test-pmd']

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def tcpdump_start_sniffing(self, ifaces=[]):
        """
        Starts tcpdump in the background to sniff the tester interface where
        the packets are transmitted to and from the self.dut.
        All the captured packets are going to be stored in a file for a
        post-analysis.
        """

        for iface in ifaces:
            command = ('tcpdump -w /tmp/tcpdump_{0}.pcap -i {0} 2>tcpdump_{0}.out &').format(iface)
            del_cmd = ('rm -f /tmp/tcpdump_{0}.pcap').format(iface)
            self.tester.send_expect(del_cmd, '#')
            self.tester.send_expect(command, '#')

    def tcpdump_stop_sniff(self):
        """
        Stops the tcpdump process running in the background.
        """
        self.tester.send_expect('killall tcpdump', '#')
        time.sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', '#')
        time.sleep(1)

    def tcpdump_command(self, command):
        """
        Sends a tcpdump related command and returns an integer from the output
        """

        result = self.tester.send_expect(command, '#')
        return int(result.strip())

    def number_of_packets(self, iface):
        """
        By reading the file generated by tcpdump it counts how many packets were
        forwarded by the sample app and received in the self.tester. The sample app
        will add a known MAC address for the test to look for.
        """

        command = ('tcpdump -A -nn -e -v -r /tmp/tcpdump_{iface}.pcap 2>/dev/null | ' +
                   'grep -c "seq"')
        return self.tcpdump_command(command.format(**locals()))

    def tcpdump_scanner(self, scanner):
        """
        Execute scanner to return results
        """
        scanner_result = self.tester.send_expect(scanner, '#', 60)
        fially_result = re.findall(r'length( \d+)', scanner_result)
        return list(fially_result)

    def number_of_bytes(self, iface):
        """
        Get the length of loading_sizes
        """
        scanner = ('tcpdump  -vv -r /tmp/tcpdump_{iface}.pcap 2>/dev/null | grep "seq"  | grep "length"')
        return self.tcpdump_scanner(scanner.format(**locals()))

    def get_chksum_value_and_verify(self, dump_pcap, save_file, Nic_list):
        packet = Packet()
        self.pks = packet.read_pcapfile(dump_pcap, self.tester)
        for i in range(len(self.pks)):
            self.pks = packet.read_pcapfile(dump_pcap, self.tester)
            pks = self.pks[i]
            out = pks.show
            chksum_list = re.findall(r'chksum=(0x\w+)', str(out))
            pks['IP'].chksum=None
            if "VXLAN" in str(out):
                pks['UDP'].chksum=None
                pks['VXLAN']['IP'].chksum=None
                pks['VXLAN']['TCP'].chksum=None
            elif "GRE" in str(out):
                pks['GRE']['IP'].chksum=None
                pks['GRE']['TCP'].chksum=None
            packet.save_pcapfile(self.tester, filename=save_file)
            self.pks1 = packet.read_pcapfile(save_file, self.tester)
            out1 = self.pks1[i].show
            chksum_list1 = re.findall(r'chksum=(0x\w+)', str(out1))
            self.tester.send_expect("rm -rf %s" % save_file, "#")
            if self.nic in Nic_list and "VXLAN" in str(out):
                self.verify(chksum_list[0] == chksum_list1[0] and chksum_list[2] == chksum_list1[2] and chksum_list[3] == chksum_list1[3], \
                            "The obtained chksum value is incorrect.")
            else:
                self.verify(chksum_list == chksum_list1, "The obtained chksum value is incorrect.")

    def test_tso(self):
        """
        TSO IPv4 TCP, IPv6 TCP, VXLan testing
        """
        tx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        rx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[1]))

        mac = self.dut.get_mac_address(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/2C/2T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.coreMask = utils.create_mask(cores)

        self.tester.send_expect("ethtool -K %s rx off tx off tso off gso off gro off lro off" % tx_interface, "# ")
        self.tester.send_expect("ip l set %s up" % tx_interface, "# ")

        if (self.nic in ["cavium_a063","cavium_a064"]):
            cmd = "%s %s -- -i --rxd=512 --txd=512 --burst=32 --rxfreet=64 --mbcache=128 --portmask=%s --max-pkt-len=%s --txpt=36 --txht=0 --txwt=0 --txfreet=32 --txrst=32 --tx-offloads=0x8000" % (self.path, self.eal_param, self.portMask, TSO_MTU)
        else:
            cmd = "%s %s -- -i --rxd=512 --txd=512 --burst=32 --rxfreet=64 --mbcache=128 --portmask=%s --max-pkt-len=%s --txpt=36 --txht=0 --txwt=0 --txfreet=32 --txrst=32 " % (self.path, self.eal_param, self.portMask, TSO_MTU)

        self.dut.send_expect(cmd, "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("port stop all", "testpmd> ", 120)
        self.dut.send_expect("csum set ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum set udp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum set tcp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        if (self.nic not in ["cavium_a063", "cavium_a064"]):
            self.dut.send_expect("csum set sctp hw %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum set outer-ip hw %d" % self.dut_ports[0], "testpmd> ", 120)

        self.dut.send_expect("csum parse-tunnel on %d" % self.dut_ports[0], "testpmd> ", 120)

        self.dut.send_expect("csum set ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum set udp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum set tcp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        if (self.nic not in ["cavium_a063", "cavium_a064"]):
            self.dut.send_expect("csum set sctp hw %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("csum set outer-ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum parse-tunnel on %d" % self.dut_ports[1], "testpmd> ", 120)

        self.dut.send_expect("tso set 800 %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("set fwd csum", "testpmd> ", 120)
        self.dut.send_expect("port start all", "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ")

        self.tester.scapy_foreground()
        time.sleep(5)

        for loading_size in self.loading_sizes:
            # IPv4 tcp test
            self.tcpdump_start_sniffing([tx_interface, rx_interface])
            out = self.dut.send_expect("clear port stats all", "testpmd> ", 120)
            self.tester.scapy_append('sendp([Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2")/TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (mac, loading_size, tx_interface))
            out = self.tester.scapy_execute()
            out = self.dut.send_expect("show port stats all", "testpmd> ", 120)
            print(out)
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(rx_interface)
            tx_stats = self.number_of_packets(tx_interface)
            tx_outlist = self.number_of_bytes(rx_interface)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "IPV6 RX or TX packet number not correct")
            else:
                num = int(loading_size/800)
                for i in range(num):
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)

        for loading_size in self.loading_sizes:
            # IPv6 tcp test
            self.tcpdump_start_sniffing([tx_interface, rx_interface])
            out = self.dut.send_expect("clear port stats all", "testpmd> ", 120)
            self.tester.scapy_append('sendp([Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="FE80:0:0:0:200:1FF:FE00:200", dst="3555:5555:6666:6666:7777:7777:8888:8888")/TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (mac, loading_size, tx_interface))
            out = self.tester.scapy_execute()
            out = self.dut.send_expect("show port stats all", "testpmd> ", 120)
            print(out)
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(rx_interface)
            tx_stats = self.number_of_packets(tx_interface)
            tx_outlist = self.number_of_bytes(rx_interface)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "IPV6 RX or TX packet number not correct")
            else:
                num = int(loading_size/800)
                for i in range(num):
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)

    def test_tso_tunneling(self):
        """
        TSO IPv4 TCP, IPv6 TCP, VXLan testing
        """
        tx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        rx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[1]))

        Nic_list = ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortville_25g"]
        save_file = "/tmp/save.pcap"
        dump_pcap = "/tmp/tcpdump_%s.pcap" % rx_interface

        mac = self.dut.get_mac_address(self.dut_ports[0])

        cores = self.dut.get_core_list("1S/2C/2T")
        self.verify(cores is not None, "Insufficient cores for speed testing")
        self.coreMask = utils.create_mask(cores)

        self.tester.send_expect("ethtool -K %s rx off tx off tso off gso off gro off lro off" % tx_interface, "# ")
        self.tester.send_expect("ip l set %s up" % tx_interface, "# ")

        cmd = "%s %s -- -i --rxd=512 --txd=512 --burst=32 --rxfreet=64 --mbcache=128 --portmask=%s --max-pkt-len=%s --txpt=36 --txht=0 --txwt=0 --txfreet=32 --txrst=32 " % (self.path, self.eal_param, self.portMask, TSO_MTU)
        self.dut.send_expect(cmd, "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("port stop all", "testpmd> ", 120)
        self.dut.send_expect("csum set ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum set udp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum set tcp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum set sctp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum set outer-ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
        if self.nic in Nic_list:
            self.logger.warning("Warning: fvl serise not support outer udp.")
        else:
            self.dut.send_expect("csum set outer-udp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.dut.send_expect("csum parse-tunnel on %d" % self.dut_ports[0], "testpmd> ", 120)

        self.dut.send_expect("csum set ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum set udp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum set tcp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum set sctp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum set outer-ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
        if self.nic in Nic_list:
            self.logger.warning("Warning: fvl serise not support outer udp.")
        else:
            self.dut.send_expect("csum set outer-udp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("csum parse-tunnel on %d" % self.dut_ports[1], "testpmd> ", 120)

        self.dut.send_expect("tunnel_tso set 800 %d" % self.dut_ports[1], "testpmd> ", 120)
        self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd> ", 120)
        self.dut.send_expect("set fwd csum", "testpmd> ", 120)
        self.dut.send_expect("port start all", "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ")

        self.tester.scapy_foreground()
        time.sleep(5)

        for loading_size in self.loading_sizes:
            # Vxlan test
            self.tcpdump_start_sniffing([tx_interface, rx_interface])
            out = self.dut.send_expect("clear port stats all", "testpmd> ", 120)
            self.tester.scapy_append('sendp([Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2")/UDP(sport=1021,dport=4789)/VXLAN()/Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2")/TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (mac, mac, loading_size, tx_interface))
            out = self.tester.scapy_execute()
            out = self.dut.send_expect("show port stats all", "testpmd> ", 120)
            print(out)
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(rx_interface)
            tx_stats = self.number_of_packets(tx_interface)
            tx_outlist = self.number_of_bytes(rx_interface)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "Vxlan RX or TX packet number not correct")
            else:
                num = int(loading_size/800)
                for i in range(num):
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)
            self.get_chksum_value_and_verify(dump_pcap, save_file, Nic_list)

        for loading_size in self.loading_sizes:
            # Nvgre test
            self.tcpdump_start_sniffing([tx_interface, rx_interface])
            out = self.dut.send_expect("clear port stats all", "testpmd> ", 120)
            self.tester.scapy_append('sendp([Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2",proto=47)/GRE(key_present=1,proto=0x6558,key=0x00001000)/Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2")/TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (mac, mac, loading_size, tx_interface))
            out = self.tester.scapy_execute()
            out = self.dut.send_expect("show port stats all", "testpmd> ", 120)
            print(out)
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(rx_interface)
            tx_stats = self.number_of_packets(tx_interface)
            tx_outlist = self.number_of_bytes(rx_interface)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "Nvgre RX or TX packet number not correct")
            else:
                num = int(loading_size/800)
                for i in range(num):
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)
            self.get_chksum_value_and_verify(dump_pcap, save_file, Nic_list)

    def test_perf_TSO_2ports(self):
        """
        TSO Performance Benchmarking with 2 ports.
        """

        # prepare traffic generator input
        tgen_input = []

        # run testpmd for each core config
        for test_cycle in self.test_cycles:
            core_config = test_cycle['cores']
            cores = self.dut.get_core_list(core_config, socket=self.ports_socket)
            self.coreMask = utils.create_mask(cores)
            if len(cores) > 2:
                queues = len(cores) // 2
            else:
                queues = 1

            command_line = "%s %s -- -i --rxd=512 --txd=512 --burst=32 --rxfreet=64 --mbcache=128 --portmask=%s --max-pkt-len=%s --txpt=36 --txht=0 --txwt=0 --txfreet=32 --txrst=32 " % (self.path, self.eal_param, self.portMask, TSO_MTU)
            info = "Executing PMD using %s\n" % test_cycle['cores']
            self.logger.info(info)
            self.rst_report(info, annex=True)
            self.rst_report(command_line + "\n\n", frame=True, annex=True)

            self.dut.send_expect(command_line, "testpmd> ", 120)
            self.dut.send_expect("port stop all", "testpmd> ", 120)
            self.dut.send_expect("csum set ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum set udp hw %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum set tcp hw %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum set sctp hw %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum set outer-ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum parse-tunnel on %d" % self.dut_ports[0], "testpmd> ", 120)
            self.dut.send_expect("csum set ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("csum set udp hw %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("csum set tcp hw %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("csum set sctp hw %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("csum set outer-ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("csum parse-tunnel on %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("tso set 800 %d" % self.dut_ports[1], "testpmd> ", 120)
            self.dut.send_expect("set fwd csum", "testpmd> ", 120)
            self.dut.send_expect("port start all", "testpmd> ", 120)
            self.dut.send_expect("set promisc all off", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ")
            for loading_size in self.loading_sizes:
                frame_size = loading_size + self.headers_size
                wirespeed = self.wirespeed(self.nic, frame_size, 2)

                # create pcap file
                self.logger.info("Running with frame size %d " % frame_size)
                payload_size = frame_size - self.headers_size
                for _port in range(2):
                    mac = self.dut.get_mac_address(self.dut_ports[_port])

                    pcap = os.sep.join([self.output_path, "dts{0}.pcap".format(_port)])
                    self.tester.scapy_append('wrpcap("%s", [Ether(dst="%s",src="52:00:00:00:00:01")/IP(src="192.168.1.1",dst="192.168.1.2")/TCP(sport=1021,dport=1021)/("X"*%d)])' % (pcap, mac, payload_size))
                    tgen_input.append((self.tester.get_local_port(self.dut_ports[_port]),
                    self.tester.get_local_port(self.dut_ports[1-_port]), "%s" % pcap))
                self.tester.scapy_execute()

                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                                                    None, self.tester.pktgen)
                _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

                pps /= 1000000.0
                test_cycle['Mpps'][loading_size] = pps
                test_cycle['pct'][loading_size] = pps * 100 // wirespeed

            self.dut.send_expect("stop", "testpmd> ")
            self.dut.send_expect("quit", "# ", 30)
            time.sleep(5)

        for n in range(len(self.test_cycles)):
            for loading_size in self.loading_sizes:
                self.verify(self.test_cycles[n]['Mpps'][
                            loading_size] > 0, "No traffic detected")

        # Print results
        self.result_table_create(self.table_header)
        for loading_size in self.loading_sizes:
            table_row = [loading_size]
            for test_cycle in self.test_cycles:
                table_row.append(test_cycle['Mpps'][loading_size])
                table_row.append(test_cycle['pct'][loading_size])

            self.result_table_add(table_row)

        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("quit", "# ")
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0])), DEFAULT_MUT), "# ")
