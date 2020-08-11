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

Test DPDK2.3 feature:
1.Fortville support granularity configuration of RSS.
By default Fortville uses hash input set preloaded from NVM image which includes all fields
- IPv4/v6+TCP/UDP port. Potential problem for this is global configuration per device and can
affect all ports. It is required that hash input set can be configurable,  such as using IPv4
only or IPv6 only or IPv4/v6+TCP/UDP.

2.Fortville support 32-bit GRE keys.
By default Fortville extracts only 24 bits of GRE key to FieldVector (NVGRE use case) but
for Telco use cases full 32-bit GRE key is needed. It is required that both 24-bit and 32-bit
keys for GRE should be supported. the test plan is to test the API to switch between 24-bit and
32-bit keys

Support 4*10G, 1*40G and 2*40G NICs.
"""
import time
import random
import re
import utils
import dut
from pmd_output import PmdOutput

testQueues = [16]
reta_entries = []
reta_lines = []

# Use scapy to send packets with different source and dest ip.
# and collect the hash result of five tuple and the queue id.
from test_case import TestCase
#
#
# Test class.
#


class TestFortvilleRssGranularityConfig(TestCase):
    #
    #
    # Utility methods and other non-test code.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                    "fortville_spirit_single", "fortville_25g", "carlsville"],
                    "NIC Unsupported: " + str(self.nic))
        ports = self.dut.get_ports(self.nic)
        self.verify(len(ports) >= 1, "Not enough ports available")
        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        self.itf = self.tester.get_interface(localPort)
        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        Run before each test case.
        """
        global reta_lines
        reta_lines = []

    def send_packet(self, itf, tran_type, inputsets=[]):
        """
        Sends packets.
        """
        global reta_lines
        self.tester.scapy_foreground()
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)

        if ('ipv4-dst-only' in inputsets):
            dstip4 = '"192.168.0.2"'
        else:
            dstip4 = 'RandIP()'
        if ('ipv4-src-only' in inputsets):
            srcip4 = '"192.168.0.1"'
        else:
            srcip4 = 'RandIP()'
        if ('ipv6-dst-only' in inputsets):
            dstip6 = '"3ffe:2501:200:3::2"'
        else:
            dstip6 = 'RandIP6()'
        if ('ipv6-src-only' in inputsets):
            srcip6 = '"3ffe:2501:200:1fff::1"'
        else:
            srcip6 = 'RandIP6()'
        if ('l4-dst-only' in inputsets):
            dstport = '1025'
        else:
            dstport = 'RandShort()'
        if ('l4-src-only' in inputsets):
            srcport = '1024'
        else:
            srcport = 'RandShort()'

        # send packet with different source and dest ip
        if tran_type == "ipv4-other":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src=' % (mac, itf)
            packet += srcip4
            packet += r', dst='
            packet += dstip4
            packet += r', proto=47)/GRE(key_present=1,proto=2048,key=67108863)/IP()], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-tcp":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src=' % (mac, itf)
            packet += srcip4
            packet += r', dst='
            packet += dstip4
            packet += r')/TCP(sport='
            packet += srcport
            packet += r',dport='
            packet += dstport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-tcp-sym":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src=' % (mac, itf)
            packet += dstip4
            packet += r', dst='
            packet += srcip4
            packet += r')/TCP(sport='
            packet += dstport
            packet += r',dport='
            packet += srcport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-udp":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src=' % (mac, itf)
            packet += srcip4
            packet += r', dst='
            packet += dstip4
            packet += r')/UDP(sport='
            packet += srcport
            packet += r',dport='
            packet += dstport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-sctp":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src=' % (mac, itf)
            packet += srcip4
            packet += r', dst='
            packet += dstip4
            packet += r')/SCTP(sport='
            packet += srcport
            packet += r',dport='
            packet += dstport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-other":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src=' % (mac, itf)
            packet += srcip6
            packet += r', dst='
            packet += dstip6
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-tcp":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src=' % (mac, itf)
            packet += srcip6
            packet += r', dst='
            packet += dstip6
            packet += r')/TCP(sport='
            packet += srcport
            packet += r',dport='
            packet += dstport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-udp":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src=' % (mac, itf)
            packet += srcip6
            packet += r', dst='
            packet += dstip6
            packet += r')/UDP(sport='
            packet += srcport
            packet += r',dport='
            packet += dstport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-sctp":
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src=' % (mac, itf)
            packet += srcip6
            packet += r', dst='
            packet += dstip6
            packet += r')/SCTP(sport='
            packet += srcport
            packet += r',dport='
            packet += dstport
            packet += r')], iface="%s")' % (itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        else:
            print("\ntran_type error!\n")

        out = self.dut.get_session_output(timeout=1)
        self.dut.send_expect("stop", "testpmd>")
        lines = out.split("\r\n")
        reta_line = {}
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.strip().startswith("port "):
                reta_line = {}
                rexp = r"port (\d)/queue (\d{1,2}): received (\d) packets"
                m = re.match(rexp, line.strip())
                if m:
                    reta_line["port"] = m.group(1)
                    reta_line["queue"] = m.group(2)

            elif len(line) != 0 and line.startswith(("src=",)):
                for item in line.split("-"):
                    item = item.strip()
                    if(item.startswith("RSS hash")):
                        name, value = item.split("=", 1)

                reta_line[name.strip()] = value.strip()
                reta_lines.append(reta_line)

        self.append_result_table()

    def append_result_table(self):
        """
        Append the hash value and queue id into table.
        """

        global reta_lines

        # append the the hash value and queue id into table
        self.result_table_create(
            ['packet index', 'hash value', 'hash index', 'queue id'])
        i = 0

        for tmp_reta_line in reta_lines:

            # compute the hash result of five tuple into the 7 LSBs value.
            hash_index = int(tmp_reta_line["RSS hash"], 16)
            self.result_table_add(
                [i, tmp_reta_line["RSS hash"], hash_index, tmp_reta_line["queue"]])
            i = i + 1

    def start_testpmd(self):
        """
        Create testpmd command
        """
        self.dut.send_expect(
            "./%s/app/testpmd  -c fffff -n %d -- -i --coremask=0xffffe --portmask=0x1 --rxq=4 --txq=4" %
            (self.target, self.dut.get_memory_channels()), "testpmd> ", 120)

        self.dut.send_expect("set verbose 8", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        res = self.pmdout.wait_link_status_up("all")
        self.verify(res is True, "link is down")

    def test_global_hash_configuration(self):
        """
        Test with flow type ipv4-tcp.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable default input set
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues end func simple_xor / end", "testpmd> ")
            
        out = self.dut.send_expect("get_hash_global_config 0", "testpmd>")
        result_scanner = r"Hash function is Simple XOR"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(out)
        if m:
            self.verify(1, "Pass")
        else:
            self.verify(0, "Fail")

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd>")
        out = self.dut.send_expect("get_hash_global_config 0", "testpmd>")
        rexp = r"Hash function is Toeplitz"
        scanner = re.compile(rexp, re.DOTALL)
        m = scanner.search(out)
        if m:
            self.verify(1, "Pass")
        else:
            self.verify(0, "Fail")

    def test_symmetric_hash_configuration(self):
        """
        Test with flow type ipv4-tcp.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable default input set
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end func symmetric_toeplitz queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp-sym", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv4_tcp_src_ipv4(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_ipv4(self):
        """
        Test with flow type ipv4-tcp and input set dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_src_port(self):
        """
        Test with flow type ipv4-tcp and input set src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_port(self):
        """
        Test with flow type ipv4-tcp and input set dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_src_ipv4(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_src_ipv4_src_port(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_src_ipv4_dst_port(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_ipv4_src_port(self):
        """
        Test with flow type ipv4-tcp and input set dst-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_ipv4_dst_port(self):
        """
        Test with flow type ipv4-tcp and input set dst-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_src_port(self):
        """
        Test with flow type ipv4-tcp and input set src-port, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l4-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_src_dst_ipv4_src_port(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, dst-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_src_dst_ipv4_dst_port(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, dst-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_src_ipv4_src_dst_port(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_dst_ipv4_src_dst_port(self):
        """
        Test with flow type ipv4-tcp and input set dst-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_tcp_all_input_set(self):
        """
        Test with flow type ipv4-tcp and input set src-ipv4, dst-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-src-only l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv4_udp_src_ipv4(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_ipv4(self):
        """
        Test with flow type ipv4-udp and input set dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_src_port(self):
        """
        Test with flow type ipv4-udp and input set src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_port(self):
        """
        Test with flow type ipv4-udp and input set dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_src_ipv4(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_src_ipv4_src_port(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_src_ipv4_dst_port(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_ipv4_src_port(self):
        """
        Test with flow type ipv4-udp and input set dst-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_ipv4_dst_port(self):
        """
        Test with flow type ipv4-udp and input set dst-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_src_port(self):
        """
        Test with flow type ipv4-udp and input set src-port, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l4-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_src_dst_ipv4_src_port(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, dst-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_src_dst_ipv4_dst_port(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, dst-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_src_ipv4_src_dst_port(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_dst_ipv4_src_dst_port(self):
        """
        Test with flow type ipv4-udp and input set dst-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_udp_all_input_set(self):
        """
        Test with flow type ipv4-udp and input set src-ipv4, dst-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv4_sctp_src_ipv4(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_ipv4(self):
        """
        Test with flow type ipv4-sctp and input set dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_src_port(self):
        """
        Test with flow type ipv4-sctp and input set src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_port(self):
        """
        Test with flow type ipv4-sctp and input set dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_src_ipv4(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_src_ipv4_src_port(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_src_ipv4_dst_port(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_ipv4_src_port(self):
        """
        Test with flow type ipv4-sctp and input set dst-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_ipv4_dst_port(self):
        """
        Test with flow type ipv4-sctp and input set dst-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_src_port(self):
        """
        Test with flow type ipv4-sctp and input set src-port, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l4-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_src_dst_ipv4_src_port(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, dst-ipv4, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_src_dst_ipv4_dst_port(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, dst-ipv4, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_src_ipv4_src_dst_port(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_dst_ipv4_src_dst_port(self):
        """
        Test with flow type ipv4-sctp and input set dst-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_sctp_all_input_set(self):
        """
        Test with flow type ipv4-sctp and input set src-ipv4, dst-ipv4, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp l3-src-only l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv6_tcp_src_ipv6(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_ipv6(self):
        """
        Test with flow type ipv6-tcp and input set dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_src_port(self):
        """
        Test with flow type ipv6-tcp and input set src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_port(self):
        """
        Test with flow type ipv6-tcp and input set dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_src_ipv6(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_src_ipv6_src_port(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_src_ipv6_dst_port(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_ipv6_src_port(self):
        """
        Test with flow type ipv6-tcp and input set dst-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_ipv6_dst_port(self):
        """
        Test with flow type ipv6-tcp and input set dst-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_src_port(self):
        """
        Test with flow type ipv6-tcp and input set src-port, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l4-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_src_dst_ipv6_src_port(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, dst-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_src_dst_ipv6_dst_port(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, dst-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_src_ipv6_src_dst_port(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_dst_ipv6_src_dst_port(self):
        """
        Test with flow type ipv6-tcp and input set dst-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_tcp_all_input_set(self):
        """
        Test with flow type ipv6-tcp and input set src-ipv6, dst-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp l3-src-only l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-tcp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv6_udp_src_ipv6(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_ipv6(self):
        """
        Test with flow type ipv6-udp and input set dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_src_port(self):
        """
        Test with flow type ipv6-udp and input set src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_port(self):
        """
        Test with flow type ipv6-udp and input set dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_src_ipv6(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_src_ipv6_src_port(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_src_ipv6_dst_port(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_ipv6_src_port(self):
        """
        Test with flow type ipv6-udp and input set dst-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_ipv6_dst_port(self):
        """
        Test with flow type ipv6-udp and input set dst-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_src_port(self):
        """
        Test with flow type ipv6-udp and input set src-port, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l4-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_src_dst_ipv6_src_port(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, dst-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_src_dst_ipv6_dst_port(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, dst-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_src_ipv6_src_dst_port(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_dst_ipv6_src_dst_port(self):
        """
        Test with flow type ipv6-udp and input set dst-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_udp_all_input_set(self):
        """
        Test with flow type ipv6-udp and input set src-ipv6, dst-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp l3-src-only l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-udp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv6_sctp_src_ipv6(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_ipv6(self):
        """
        Test with flow type ipv6-sctp and input set dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_src_port(self):
        """
        Test with flow type ipv6-sctp and input set src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_port(self):
        """
        Test with flow type ipv6-sctp and input set dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_src_ipv6(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_src_ipv6_src_port(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_src_ipv6_dst_port(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_ipv6_src_port(self):
        """
        Test with flow type ipv6-sctp and input set dst-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_ipv6_dst_port(self):
        """
        Test with flow type ipv6-sctp and input set dst-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_src_port(self):
        """
        Test with flow type ipv6-sctp and input set src-port, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-port, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l4-src-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['l4-src-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_src_dst_ipv6_src_port(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, dst-ipv6, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l3-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_src_dst_ipv6_dst_port(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, dst-ipv6, dst-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, dst-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l3-dst-only l4-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-dst-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_src_ipv6_src_dst_port(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_dst_ipv6_src_dst_port(self):
        """
        Test with flow type ipv6-sctp and input set dst-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_sctp_all_input_set(self):
        """
        Test with flow type ipv6-sctp and input set src-ipv6, dst-ipv6, dst-port, src-port.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6, dst-port, src-port
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp l3-src-only l3-dst-only l4-dst-only l4-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only', 'l4-dst-only', 'l4-src-only']
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-sctp", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv4_other_src_ipv4(self):
        """
        Test with flow type ipv4-other and input set src-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only']
        self.send_packet(self.itf, "ipv4-other", inputsets)
        self.send_packet(self.itf, "ipv4-other", inputsets)
        self.send_packet(self.itf, "ipv4-other", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-other", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_other_dst_ipv4(self):
        """
        Test with flow type ipv4-other and input set dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-other", inputsets)
        self.send_packet(self.itf, "ipv4-other", inputsets)
        self.send_packet(self.itf, "ipv4-other", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-other", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv4_other_dst_src_ipv4(self):
        """
        Test with flow type ipv4-other and input set src-ipv4, dst-ipv4.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv4, dst-ipv4
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv4-src-only', 'ipv4-dst-only']
        self.send_packet(self.itf, "ipv4-other", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv4-other", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_ipv6_other_src_ipv6(self):
        """
        Test with flow type ipv6-other and input set src-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other l3-src-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only']
        self.send_packet(self.itf, "ipv6-other", inputsets)
        self.send_packet(self.itf, "ipv6-other", inputsets)
        self.send_packet(self.itf, "ipv6-other", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-other", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_other_dst_ipv6(self):
        """
        Test with flow type ipv6-other and input set dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-other", inputsets)
        self.send_packet(self.itf, "ipv6-other", inputsets)
        self.send_packet(self.itf, "ipv6-other", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-other", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] != result_rows[3][1]) or (result_rows[1][3] != result_rows[3][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")
        elif ((result_rows[1][1] == result_rows[4][1]) and (result_rows[1][3] == result_rows[4][3])):
            flag = 0
            self.verify(flag, "The two hash values are same, rss_granularity_config failed!")

    def test_ipv6_other_dst_src_ipv6(self):
        """
        Test with flow type ipv6-other and input set src-ipv6, dst-ipv6.
        """
        flag = 1

        self.start_testpmd()

        # set hash input set by testpmd on dut, enable src-ipv6, dst-ipv6
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other l3-src-only l3-dst-only end queues end / end", "testpmd> ")
        inputsets = ['ipv6-src-only', 'ipv6-dst-only']
        self.send_packet(self.itf, "ipv6-other", inputsets)

        self.dut.send_expect(
            "flow destroy 0 rule 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end", "testpmd> ")
        self.send_packet(self.itf, "ipv6-other", inputsets)

        self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        if ((result_rows[1][1] != result_rows[2][1]) or (result_rows[1][3] != result_rows[2][3])):
            flag = 0
            self.verify(flag, "The two hash values are different, rss_granularity_config failed!")

    def test_flow_validate(self):
        """
        Test the flow rule validate.
        """
        self.start_testpmd()

        out = self.dut.send_expect("flow validate 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end queues end / end", "testpmd> ")
        self.verify("Flow rule validated" in out, "Failed to validated!")

        out = self.dut.send_expect("flow validate 0 ingress pattern end actions rss types end queues 0 1 end / end", "testpmd> ")
        self.verify("Flow rule validated" in out, "Failed to validated!")
        
        out = self.dut.send_expect("flow validate 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp l3-dst-only end queues 0 1 end / end", "testpmd> ")
        self.verify("Flow rule validated" not in out, "Failed to validated!")

        self.dut.send_expect("quit", "# ", 30)

    def test_flow_query(self):
        """
        Test the flow rule query.
        """
        self.start_testpmd()

        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end", "testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp l3-src-only end queues end func symmetric_toeplitz / end", "testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern end actions rss types end queues end func simple_xor / end", "testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern end actions rss types end queues 1 2 end / end", "testpmd> ")

        rexp = r"flow query 0 (\d) rss\r\r\nRSS:\r\n queues: ([\S\s]+?)\r\n function: (\S+?)\r\n types:\r\n  ([\s\S]+)"
        out0 = self.dut.send_expect("flow query 0 0 rss", "testpmd> ")
        m0 = re.match(rexp, out0.strip())
        self.verify("none" == m0.group(2) and "default" == m0.group(3) and "ipv4-tcp" == m0.group(4) , "Query error")
        out1 = self.dut.send_expect("flow query 0 1 rss", "testpmd> ")
        m1 = re.match(rexp, out1.strip())
        self.verify("none" == m1.group(2) and "symmetric_toeplitz" == m1.group(3) and "ipv4-udp" in m1.group(4) and "l3-src-only" in m1.group(4) , "Query error")
        out2 = self.dut.send_expect("flow query 0 2 rss", "testpmd> ")
        m2 = re.match(rexp, out2.strip())
        self.verify("none" == m2.group(2) and "simple_xor" == m2.group(3) and "none" == m2.group(4) , "Query error")
        out3 = self.dut.send_expect("flow query 0 3 rss", "testpmd> ")
        m3 = re.match(rexp, out3.strip())
        self.verify("1 2" == m3.group(2) and "default" == m3.group(3) and "none" == m3.group(4) , "Query error")

        self.dut.send_expect("flow flush 0", "testpmd> ")
        out4 = self.dut.send_expect("flow query 0 0 rss", "testpmd> ")
        self.verify("Flow rule #0 not found" in out4, "Failed to rss query!")

        self.dut.send_expect("quit", "# ", 30)

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
