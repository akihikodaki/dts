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

Test DPDK1.8 feature: Fortville RSS full support - configuring hash functions.
It can select Toeplitz or simple XOR hash function and it can configure symmetric hash functions.
Support 4*10G, 1*40G and 2*40G NICs.
"""
import time
import random
import re
import utils

queue = 16
reta_entries = []
reta_num = 128
iptypes = {'ipv4-sctp': 'sctp',
           'ipv4-other': 'ip',
           'ipv4-frag': 'ip',
           'ipv4-udp': 'udp',
           'ipv4-tcp': 'tcp',
           # this hash not support in dpdk2.0
           # 'l2_payload':'ether',
           'ipv6-other': 'ip',
           'ipv6-sctp': 'sctp',
           'ipv6-udp': 'udp',
           'ipv6-tcp': 'tcp',
           'ipv6-frag': 'ip'
           }

# Use scapy to send packets with different source and dest ip.
# and collect the hash result of five tuple and the queue id.
from test_case import TestCase
#
#
# Test class.
#
class TestPmdrssHash(TestCase):
    #
    #
    # Utility methods and other non-test code.
    #
    def send_packet(self, itf, tran_type):
        """
        Sends packets.
        """
        received_pkts = []
        self.tester.scapy_foreground()
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)

        # send packet with different source and dest ip
        if tran_type == "ipv4-other":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-tcp":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-udp":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-sctp":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1024,dport=1024,tag=1)], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-frag":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d",frag=1,flags="MF")], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "l2_payload":
            for i in range(10):
                packet = r'sendp([Ether(src="00:00:00:00:00:0%d",dst="%s")], iface="%s")' % (
                    i + 1, mac, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)

        elif tran_type == "ipv6-other":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-tcp":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/TCP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-udp":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-sctp":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(sport=1024,dport=1024,tag=1)], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-frag":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d",nh=44)/IPv6ExtHdrFragment()], iface="%s")' % (
                    mac, itf, i + 1, i + 2, itf)
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
                if "RSS hash" not in line:
                    continue
                for item in line.split("-"):
                    item = item.strip()
                    if(item.startswith("RSS hash")):
                        name, value = item.split("=", 1)

                reta_line[name.strip()] = value.strip()
                received_pkts.append(reta_line)

        self.verifyResult(received_pkts)

    def verifyResult(self, reta_lines):
        """
        Verify whether or not the result passes.
        """

        global reta_num
        result = []
        self.verify(len(reta_lines) > 0, 'No packet received!')
        self.result_table_create(
            ['packet index', 'hash value', 'hash index', 'queue id', 'actual queue id', 'pass '])

        i = 0

        for tmp_reta_line in reta_lines:
            status = "false"
            # compute the hash result of five tuple into the 7 LSBs value.
            hash_index = int(tmp_reta_line["RSS hash"], 16) % reta_num
            print(reta_entries[hash_index], tmp_reta_line)
            if(reta_entries[hash_index] == int(tmp_reta_line["queue"])):
                status = "true"
                result.insert(i, 0)
            else:
                status = "fail"
                result.insert(i, 1)
            self.result_table_add(
                [i, tmp_reta_line["RSS hash"], hash_index, reta_entries[hash_index], tmp_reta_line["queue"], status])
            i = i + 1

        self.result_table_print()
        self.verify(sum(result) == 0, "the reta update function failed!")

    def send_packet_symmetric(self, itf, tran_type):
        """
        Sends packets.
        """
        received_pkts = []
        self.tester.scapy_foreground()
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)

        # send packet with different source and dest ip
        if tran_type == "ipv4-other":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)

        elif tran_type == "ipv4-tcp":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1025)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1025,dport=1024)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-udp":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1025)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1025,dport=1024)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-sctp":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1024,dport=1025,tag=1)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1025,dport=1024,tag=1)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-frag":
            for i in range(10):
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d",frag=1,flags="MF")], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d",frag=1,flags="MF")], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "l2_payload":
            for i in range(10):
                packet = r'sendp([Ether(src="00:00:00:00:00:%02d",dst="%s")], iface="%s")' % (
                    i + 1, mac, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-other":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:3::%d", dst="3ffe:2501:200:1fff::%d")], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)

        elif tran_type == "ipv6-tcp":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/TCP(sport=1024,dport=1025)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:3::%d", dst="3ffe:2501:200:1fff::%d")/TCP(sport=1025,dport=1024)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)

        elif tran_type == "ipv6-udp":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(sport=1024,dport=1025)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(sport=1025,dport=1024)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-sctp":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(sport=1024,dport=1025,tag=1)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(sport=1025,dport=1024,tag=1)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-frag":
            for i in range(4):
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d",nh=44)/IPv6ExtHdrFragment()], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet2 = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d",nh=44)/IPv6ExtHdrFragment()], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(.5)
        else:
            print("\ntran_type error!\n")

        out = self.dut.get_session_output(timeout=1)
        self.dut.send_expect("stop", "testpmd>")
        lines = out.split("\r\n")

        # collect the hash result of five tuple and the queue id
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
                    else:
                        continue

                reta_line[name.strip()] = value.strip()
                received_pkts.append(reta_line)

        self.verifyResult_symmetric(received_pkts)

    def verifyResult_symmetric(self, reta_lines):
        """
        Verify whether or not the result passes.
        """

        global reta_num
        result = []
        self.verify(len(reta_lines) > 0, 'No packet received!')
        self.result_table_create(
            ['packet index', 'RSS hash', 'hash index', 'queue id', 'actual queue id', 'pass '])

        i = 0
        for tmp_reta_line in reta_lines:
            status = "false"
            # compute the hash result of five tuple into the 7 LSBs value.
            hash_index = int(tmp_reta_line["RSS hash"], 16) % reta_num
            if(reta_entries[hash_index] == int(tmp_reta_line["queue"])):
                status = "true"
                result.insert(i, 0)
                if(i % 2 == 1):
                    if(pre_RSS_hash == tmp_reta_line["RSS hash"]):
                        status = "true"
                        result.insert(len(reta_lines) + (i - 1) // 2, 0)
                    else:
                        status = "fail"
                        result.insert(len(reta_lines) + (i - 1) // 2, 1)
                pre_RSS_hash = tmp_reta_line["RSS hash"]
            else:
                status = "fail"
                result.insert(i, 1)
            self.result_table_add(
                [i, tmp_reta_line["RSS hash"], hash_index, reta_entries[hash_index], tmp_reta_line["queue"], status])
            i = i + 1

        self.result_table_print()
        self.verify(
            sum(result) == 0, "the symmetric RSS hash function failed!")

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.verify(self.nic in ["columbiaville_25g", "columbiaville_100g","fortville_eagle", "fortville_spirit",
                    "fortville_spirit_single", "redrockcanyou", "atwood",
                    "boulderrapid", "fortpark_TLV", "fortpark_BASE-T","fortville_25g", "niantic", "carlsville", "foxville"],
                    "NIC Unsupported: " + str(self.nic))
        global reta_num
        global iptypes
        global queue
        if self.nic in ["foxville"]:
            queue = 4

        if self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortpark_TLV", "fortpark_BASE-T","fortville_25g", "carlsville"]:
            reta_num = 512
        elif self.nic in ["niantic", "foxville"]:
            reta_num = 128
            iptypes = {'ipv4-other': 'ip',
                       'ipv4-frag': 'ip',
                       'ipv4-udp': 'udp',
                       'ipv4-tcp': 'tcp',
                       'ipv6-other': 'ip',
                       'ipv6-udp': 'udp',
                       'ipv6-tcp': 'tcp',
                       'ipv6-frag': 'ip'
                       }
        elif self.nic in ["redrockcanyou", "atwood", "boulderrapid"]:
            reta_num = 128
        else:
            self.verify(False, "NIC Unsupported:%s" % str(self.nic))
        ports = self.dut.get_ports(self.nic)
        self.verify(len(ports) >= 1, "Not enough ports available")
        self.path=self.dut.apps_name['test-pmd']

    def set_up(self):
        """
        Run before each test case.
        """
        cores = self.dut.get_core_list("all")
        self.eal_para = self.dut.create_eal_parameters(cores=cores)
        self.coremask = utils.create_mask(cores)

    def test_toeplitz(self):
        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(localPort)
        global reta_num
        global iptypes

        self.dut.kill_all()

        # test with different rss queues
        self.dut.send_expect(
            "%s %s -- -i --rxq=%d --txq=%d" %
            (self.path, self.eal_para, queue, queue), "testpmd> ", 120)

        for iptype, rsstype in list(iptypes.items()):
            self.dut.send_expect("set verbose 8", "testpmd> ")
            self.dut.send_expect("set fwd rxonly", "testpmd> ")
            self.dut.send_expect("set promisc all off", "testpmd> ")
            self.dut.send_expect(
                "set nbcore %d" % (queue + 1), "testpmd> ")

            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect(
                "set_hash_global_config  0 toeplitz %s enable" % iptype, "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")
            out = self.dut.send_expect(
                "port config all rss %s" % rsstype, "testpmd> ")
            self.verify("error" not in out, "Configuration of RSS hash failed: Invalid argument")
            # configure the reta with specific mappings.
            for i in range(reta_num):
                reta_entries.insert(i, random.randint(0, queue - 1))
                self.dut.send_expect(
                    "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]), "testpmd> ")

            self.send_packet(itf, iptype)

        self.dut.send_expect("quit", "# ", 30)

    def test_toeplitz_symmetric(self):
        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(localPort)
        global reta_num
        global iptypes

        self.dut.kill_all()

        # test with different rss queues
        self.dut.send_expect(
            "%s %s -- -i --rxq=%d --txq=%d" %
            (self.path, self.eal_para, queue, queue), "testpmd> ", 120)

        for iptype, rsstype in list(iptypes.items()):
            self.dut.send_expect("set verbose 8", "testpmd> ")
            self.dut.send_expect("set fwd rxonly", "testpmd> ")
            self.dut.send_expect("set promisc all off", "testpmd> ")
            self.dut.send_expect(
                "set nbcore %d" % (queue + 1), "testpmd> ")

            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect(
                "set_hash_global_config 0 toeplitz %s enable" % iptype, "testpmd> ")
            self.dut.send_expect(
                "set_sym_hash_ena_per_port 0 enable", "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")
            out = self.dut.send_expect(
                "port config all rss %s" % rsstype, "testpmd> ")
            self.verify("error" not in out, "Configuration of RSS hash failed: Invalid argument")

            # configure the reta with specific mappings.
            for i in range(reta_num):
                reta_entries.insert(i, random.randint(0, queue - 1))
                self.dut.send_expect(
                    "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]), "testpmd> ")

            self.send_packet_symmetric(itf, iptype)

        self.dut.send_expect("quit", "# ", 30)

    def test_simple(self):
        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(localPort)
        global reta_num
        global iptypes

        if self.kdriver in ["fm10k"]:
            iptypes.pop('ipv4-sctp')
            iptypes.pop('ipv6-sctp')

        self.dut.kill_all()

        # test with different rss queues
        self.dut.send_expect(
            "%s %s -- -i --rxq=%d --txq=%d" %
            (self.path, self.eal_para, queue, queue), "testpmd> ", 120)

        for iptype, rsstype in list(iptypes.items()):
            self.logger.info("***********************%s rss test********************************" % iptype)
            self.dut.send_expect("set verbose 8", "testpmd> ")
            self.dut.send_expect("set fwd rxonly", "testpmd> ")
            self.dut.send_expect("set promisc all off", "testpmd> ")
            self.dut.send_expect(
                "set nbcore %d" % (queue + 1), "testpmd> ")

            self.dut.send_expect("port stop all", "testpmd> ")
            # some nic not support change hash algorithm
            if self.kdriver not in ["fm10k"]:
                self.dut.send_expect(
                    "set_hash_global_config 0 simple_xor %s enable" % iptype, "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")
            out = self.dut.send_expect(
                "port config all rss %s" % rsstype, "testpmd> ")
            self.verify("error" not in out, "Configuration of RSS hash failed: Invalid argument")
            # configure the reta with specific mappings.
            for i in range(reta_num):
                reta_entries.insert(i, random.randint(0, queue - 1))
                self.dut.send_expect(
                    "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]), "testpmd> ")
            self.send_packet(itf, iptype)

        self.dut.send_expect("quit", "# ", 30)

    def test_simple_symmetric(self):

        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(localPort)
        global reta_num
        global iptypes
        self.dut.kill_all()

        # test with different rss queues
        self.dut.send_expect(
            "%s %s -- -i --rxq=%d --txq=%d" %
            (self.path, self.eal_para, queue, queue), "testpmd> ", 120)

        for iptype, rsstype in list(iptypes.items()):
            self.dut.send_expect("set verbose 8", "testpmd> ")
            self.dut.send_expect("set fwd rxonly", "testpmd> ")
            self.dut.send_expect("set promisc all off", "testpmd> ")
            self.dut.send_expect(
                "set nbcore %d" % (queue + 1), "testpmd> ")

            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect(
                "set_hash_global_config 0 simple_xor %s enable" % iptype, "testpmd> ")
            self.dut.send_expect(
                "set_sym_hash_ena_per_port 0 enable", "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")

            out = self.dut.send_expect(
                "port config all rss %s" % rsstype, "testpmd> ")
            self.verify("error" not in out, "Configuration of RSS hash failed: Invalid argument")
            # configure the reta with specific mappings.
            for i in range(reta_num):
                reta_entries.insert(i, random.randint(0, queue - 1))
                self.dut.send_expect(
                    "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]), "testpmd> ")
            self.send_packet_symmetric(itf, iptype)

        self.dut.send_expect("quit", "# ", 30)

    def test_dynamic_rss_bond_config(self):
        
        # setup testpmd and finish bond config
        self.verify(self.nic in ["columbiaville_25g", "columbiaville_100g","fortville_eagle", "fortville_spirit",
                    "fortpark_TLV","fortpark_BASE-T", "fortville_25g", "carlsville", "foxville"],
                    "NIC Unsupported: " + str(self.nic))

        self.dut.send_expect("%s %s -- -i" % (self.path, self.eal_para), "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ")
        out = self.dut.send_expect("create bonded device 3 0", "testpmd> ", 30)
        bond_device_id = int(re.search("port \d+", out).group().split(" ")[-1].strip())

        self.dut.send_expect("add bonding slave 0 %d" % bond_device_id, "testpmd>", 30)
        self.dut.send_expect("add bonding slave 1 %d" % bond_device_id, "testpmd>", 30)

        # get slave device default rss hash algorithm
        out = self.dut.send_expect("get_hash_global_config 0", "testpmd>")
        slave0_hash_function = re.search("Hash function is .+", out).group().split(" ")[-1].strip()
        out = self.dut.send_expect("get_hash_global_config 1", "testpmd>")
        slave1_hash_function = re.search("Hash function is .+", out).group().split(" ")[-1].strip()
        self.verify(slave0_hash_function == slave1_hash_function, "default hash function not match")

        new_hash_function = ""
        for hash_function in ["toeplitz", "simple_xor"]:
            if slave0_hash_function[-3:].lower() != hash_function[-3:]:
                new_hash_function = hash_function
        # update slave 0 rss hash algorithm and get slave 0 and slave 1 rss new hash algorithm
        self.dut.send_expect("set_hash_global_config 0 %s ipv4-other enable" % new_hash_function, "testpmd>")
        out = self.dut.send_expect("get_hash_global_config 0", "testpmd>")
        slave0_new_hash_function = re.search("Hash function is .+", out).group().split(" ")[-1].strip()
        out = self.dut.send_expect("get_hash_global_config 1", "testpmd>")
        slave1_new_hash_function = re.search("Hash function is .+", out).group().split(" ")[-1].strip()

        self.verify(slave0_new_hash_function == slave1_new_hash_function, "bond slave auto sync hash function failed")
        self.verify(slave0_new_hash_function[-3:].lower() == new_hash_function[-3:], "changed slave hash function failed")

        self.dut.send_expect("remove bonding slave 0 %d" % bond_device_id, "testpmd>", 30)
        self.dut.send_expect("remove bonding slave 1 %d" % bond_device_id, "testpmd>", 30)
        self.dut.send_expect("quit","# ", 30)

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
