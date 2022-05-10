# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
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

Test moving RSS to rte_flow.

"""

import re
import time

import framework.packet as packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestRSS_to_Rteflow(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        Move RSS to rte_flow Prerequisites
        """
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.pmd_output = PmdOutput(self.dut)

        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        localPort1 = self.tester.get_local_port(self.dut_ports[1])

        self.tester0_itf = self.tester.get_interface(localPort0)
        self.tester1_itf = self.tester.get_interface(localPort1)

        self.tester0_mac = self.tester.get_mac(localPort0)
        self.tester1_mac = self.tester.get_mac(localPort1)

        self.pf0_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf1_interface = self.dut.ports_info[self.dut_ports[1]]["intf"]

        self.pf0_mac = self.dut.get_mac_address(0)
        self.pf1_mac = self.dut.get_mac_address(1)
        self.pf0_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.pf1_pci = self.dut.ports_info[self.dut_ports[1]]["pci"]
        self.pmdout = PmdOutput(self.dut)
        self.cores = "1S/2C/1T"
        self.pkt1 = (
            "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2')/SCTP(dport=80, sport=80)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt2 = (
            "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2', proto=17)/UDP(dport=50, sport=50)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt3 = (
            "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.3')/TCP(dport=50, sport=50)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt4 = (
            "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2')/('X'*48)"
            % self.pf0_mac
        )
        self.pkt5 = (
            "Ether(dst='%s')/IPv6(src='2001::1',dst='2001::2',nh=132)/SCTP(dport=80, sport=80)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt6 = (
            "Ether(dst='%s')/IPv6(src='2001::1',dst='2001::2')/UDP(dport=50, sport=50)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt7 = (
            "Ether(dst='%s')/IPv6(src='2001::2',dst='2001::3')/TCP(dport=50, sport=50)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt8 = (
            "Ether(dst='%s')/IPv6(src='2001::2',dst='2001::3')/('X'*48)" % self.pf0_mac
        )
        self.pkt9 = (
            "Ether(dst='%s')/IP(src='10.0.0.1',dst='192.168.0.2', frag=1)/Raw('X'*48)"
            % self.pf0_mac
        )
        self.pkt10 = (
            "Ether(dst='%s')/IPv6(dst='CDCD:910A:2222:5498:8475:1111:3900:2020', nh=44)/('X'*48)"
            % self.pf0_mac
        )
        self.pkt11 = (
            "Ether(dst='%s', type=0x0807)/Raw(load='\x61\x62\x63\x64')" % self.pf0_mac
        )
        self.prio_pkt1 = (
            "Ether(dst='%s')/Dot1Q(prio=1)/IP(src='10.0.0.1',dst='192.168.0.2')/TCP(dport=80, sport=80)/('X'*48)"
            % self.pf0_mac
        )
        self.prio_pkt2 = (
            "Ether(dst='%s')/Dot1Q(prio=2)/IP(src='10.0.0.1',dst='192.168.0.2')/TCP(dport=80, sport=80)/('X'*48)"
            % self.pf0_mac
        )
        self.prio_pkt3 = (
            "Ether(dst='%s')/Dot1Q(prio=3)/IP(src='10.0.0.1',dst='192.168.0.2')/TCP(dport=80, sport=80)/('X'*48)"
            % self.pf0_mac
        )

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

    def destroy_env(self):
        """
        This is to stop testpmd.
        """
        self.dut.send_expect("quit", "# ")
        time.sleep(2)

    def get_queue_number(self, port_id=0):
        """
        get the queue which packet enter.
        """
        outstring = self.pmdout.get_output()
        print(outstring)
        scanner = re.compile(
            r"port\s?%d/queue\s?(\d+):\s?received \d+ packets" % port_id
        )
        m = scanner.search(outstring)
        queue_id = m.group(1)
        print(("queue is %s" % queue_id))
        self.dut.send_expect(
            "clear port stats all", "NIC statistics for port 1 cleared", 20
        )
        return queue_id

    def send_and_check(self, pkts, rss_queue, port_id=0):
        """
        send packet and check the result
        """
        itf = self.tester0_itf if port_id == 0 else self.tester1_itf
        queue_list = []
        if isinstance(pkts, list):
            for pkt in pkts:
                self.tester.scapy_append('sendp(%s, iface="%s")' % (pkt, itf))
                self.tester.scapy_execute()
                queue = self.get_queue_number(port_id)
                self.verify(
                    queue in rss_queue,
                    "the packet doesn't enter the expected RSS queue.",
                )
                queue_list.append(queue)
        else:
            self.tester.scapy_append('sendp(%s, iface="%s")' % (pkts, itf))
            self.tester.scapy_execute()
            queue = self.get_queue_number(port_id)
            self.verify(
                queue in rss_queue, "the packet doesn't enter the expected RSS queue."
            )
            queue_list.append(queue)
        return queue_list

    def send_packet(self, ptype, port_id=0):
        """
        Sends packets.
        """
        pkt_list = []
        if ptype == "ipv4-udp":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(dport=%d, sport=%d)'
                    % (self.pf0_mac, i + 1, i + 2, i + 21, i + 22)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv4-other":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")'
                    % (self.pf0_mac, i + 1, i + 2)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv4-tcp":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(dport=%d, sport=%d)'
                    % (self.pf0_mac, i + 1, i + 2, i + 21, i + 22)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv4-sctp":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(dport=%d, sport=%d)'
                    % (self.pf0_mac, i + 1, i + 2, i + 21, i + 22)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv4-frag":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d",frag=1,flags="MF")'
                    % (self.pf0_mac, i + 1, i + 2)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv6-other":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")'
                    % (self.pf0_mac, i + 1, i + 2)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv6-frag":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d",nh=44)/IPv6ExtHdrFragment()'
                    % (self.pf0_mac, i + 1, i + 2)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv6-udp":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(dport=%d, sport=%d)'
                    % (self.pf0_mac, i + 1, i + 2, i + 21, i + 22)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv6-tcp":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/TCP(dport=%d, sport=%d)'
                    % (self.pf0_mac, i + 1, i + 2, i + 21, i + 22)
                )
                pkt_list.append(scapy_pkt)
        elif ptype == "ipv6-sctp":
            for i in range(100):
                scapy_pkt = (
                    'Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(dport=%d, sport=%d)'
                    % (self.pf0_mac, i + 1, i + 2, i + 21, i + 22)
                )
                pkt_list.append(scapy_pkt)

        elif ptype == "l2-payload":
            for i in range(100):
                scapy_pkt = (
                    r'Ether(dst="%s", type=0x08%s)/Raw(load="\x61\x62\x63\x64")'
                    % (self.pf0_mac, str(i) if (len(str(i)) == 2) else ("0" + str(i)))
                )
                pkt_list.append(scapy_pkt)

        pkt = packet.Packet()
        pkt.update_pkt(pkt_list)
        itf = self.tester0_itf if port_id == 0 else self.tester1_itf
        pkt.send_pkt(self.tester, tx_port=itf)

    def check_packet_queue(self, queue, out, port_id=0):
        """
        get the queue which packet enter.
        """
        time.sleep(2)
        if queue == "all":
            self.verify(
                "RX Port= %d/Queue= 0" % port_id in out
                and "RX Port= %d/Queue= 1" % port_id in out
                and "RX Port= %d/Queue= 2" % port_id in out
                and "RX Port= %d/Queue= 3" % port_id in out,
                "There is some queues doesn't work.",
            )
        elif queue == "0":
            self.verify(
                "RX Port= %d/Queue= 0" % port_id in out
                and "RX Port= %d/Queue= 1" % port_id not in out
                and "RX Port= %d/Queue= 2" % port_id not in out
                and "RX Port= %d/Queue= 3" % port_id not in out,
                "RSS is enabled.",
            )

        lines = out.split("\r\n")
        reta_line = {}
        queue_flag = 0
        packet_sumnum = 0
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if queue_flag == 1:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_num = m.group(1)
                packet_sumnum = packet_sumnum + int(packet_num)
                queue_flag = 0
            elif line.strip().startswith(
                "------- Forward Stats for RX Port= %d" % port_id
            ):
                queue_flag = 1
            elif line.strip().startswith("+++++++++++++++ Accumulated"):
                queue_flag = 2
            elif line.strip().startswith("RX-packets") and queue_flag == 2:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_rec = m.group(1)

        self.verify(
            packet_sumnum == int(packet_rec) == 100, "There are some packets lost."
        )

    def send_check_100_packet_queue(self, ptype_list, queue, port_id=0):
        """
        send 100 packets and get the queues distributed result.
        """
        if isinstance(ptype_list, list):
            for ptype in ptype_list:
                self.send_packet(ptype, port_id)
                out = self.dut.send_expect("stop", "testpmd> ")
                if isinstance(queue, list):
                    self.check_packet_selected_queue(queue, out, port_id)
                else:
                    self.check_packet_queue(queue, out, port_id)
                self.dut.send_expect("start", "testpmd> ", 120)
        else:
            self.send_packet(ptype_list, port_id)
            out = self.dut.send_expect("stop", "testpmd> ", 120)
            if isinstance(queue, list):
                self.check_packet_selected_queue(queue, out, port_id)
            else:
                self.check_packet_queue(queue, out, port_id)
            self.dut.send_expect("start", "testpmd> ", 120)

    def check_packet_selected_queue(self, queues, out, port_id=0):
        """
        get the queue which packet enter.
        """
        time.sleep(2)
        for queue in queues:
            self.verify(
                "RX Port= %d/Queue= %s" % (port_id, queue) in out,
                "The packets are not distributed to expected queue.",
            )

        lines = out.split("\r\n")
        reta_line = {}
        queue_flag = 0
        packet_sumnum = 0
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if queue_flag == 1:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_num = m.group(1)
                packet_sumnum = packet_sumnum + int(packet_num)
                queue_flag = 0
            elif line.strip().startswith(
                "------- Forward Stats for RX Port= %d" % port_id
            ):
                result = re.search(
                    r"------- Forward Stats for RX Port=\s*\d*/Queue=\s*(\d*)", line
                )
                if result.group(1) in queues:
                    queue_flag = 1
            elif line.strip().startswith("+++++++++++++++ Accumulated"):
                queue_flag = 2
            elif line.strip().startswith("RX-packets") and queue_flag == 2:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_rec = m.group(1)

        self.verify(
            packet_sumnum == int(packet_rec) == 100, "There are some packets lost."
        )

    def test_set_rss_types(self):
        """
        Disable and enable RSS.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        out = self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Show port default RSS functions
        self.dut.send_expect(
            "show port 0 rss-hash", "ipv4-frag ipv4-other ipv6-frag ipv6-other"
        )
        self.dut.send_expect(
            "show port 1 rss-hash", "ipv4-frag ipv4-other ipv6-frag ipv6-other"
        )

        self.send_check_100_packet_queue("ipv4-other", "all", port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=1)

        # Enable ipv4-udp RSS hash function on port 0
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect("show port 0 rss-hash", "ipv4-udp")
        self.send_check_100_packet_queue("ipv4-other", "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)
        self.send_check_100_packet_queue("ipv4-udp", "all", port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=1)

        # Enable all RSS hash function on port 1
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / end actions rss types l2-payload end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / end actions rss types ipv6-frag end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end",
            "created",
        )

        self.dut.send_expect(
            "show port 1 rss-hash",
            "ipv4-frag ipv4-tcp ipv4-udp ipv4-sctp ipv4-other ipv6-frag ipv6-tcp ipv6-udp ipv6-sctp ipv6-other l2-payload sctp",
        )
        # send the packets and verify the results
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=1)

        ptype_list2 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "all", port_id=0)

        # Enable all RSS hash function on port 0
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / end actions rss types l2-payload end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-other end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / end actions rss types ipv4-frag end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / sctp / end actions rss types ipv4-sctp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / end actions rss types ipv6-frag end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end",
            "created",
        )

        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=1)

        # delete rule 0/2/10 of port 1
        self.dut.send_expect("flow destroy 1 rule 0", "Flow rule #0 destroyed")
        self.dut.send_expect("flow destroy 1 rule 2", "Flow rule #2 destroyed")
        self.dut.send_expect("flow destroy 1 rule 10", "Flow rule #10 destroyed")

        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)

        ptype_list3 = [
            "ipv4-other",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
        ]
        self.send_check_100_packet_queue(ptype_list3, "all", port_id=1)

        ptype_list4 = ["ipv4-frag", "ipv6-sctp", "l2-payload"]
        self.send_check_100_packet_queue(ptype_list4, "0", port_id=1)

        # flush all rules of port 0
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect("show port 0 rss-hash", "RSS disabled")
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        self.send_check_100_packet_queue(ptype_list3, "all", port_id=1)
        self.send_check_100_packet_queue(ptype_list4, "0", port_id=1)

        # flush all rules of port 1
        self.dut.send_expect("flow flush 1", "testpmd> ")
        self.dut.send_expect("show port 1 rss-hash", "RSS disabled")
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=1)

    def test_set_rss_queues(self):
        """
        Set valid and invalid parameter.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=8 --txq=8 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule on port 0
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 1 4 7 end / end",
            "created",
        )
        self.dut.send_expect(
            "show port 0 rss-hash", "ipv4-frag ipv4-other ipv6-frag ipv6-other"
        )

        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=1)
        # Create a rss queue rule on port 1
        self.dut.send_expect(
            "flow create 1 ingress pattern end actions rss types end queues 3 end / end",
            "created",
        )
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-other", ["3"], port_id=1)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=1)

        # Create a different rss queue rule on port 1
        self.dut.send_expect(
            "flow create 1 ingress pattern end actions rss types end queues 1 4 7 end / end",
            "created",
        )
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=1)

        # flush rule on port 0
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect(
            "show port 0 rss-hash", "ipv4-frag ipv4-other ipv6-frag ipv6-other"
        )
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=0)
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=1)

        # Create a rss queue rule on port 0 again
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 1 4 7 end / end",
            "created",
        )
        # delete rule 1 of port 1
        self.dut.send_expect("flow destroy 1 rule 1", "Flow rule #1 destroyed")
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)

        # Create a rss queue rule on port 1 again
        self.dut.send_expect(
            "flow create 1 ingress pattern end actions rss types end queues 3 end / end",
            "created",
        )
        # delete rule 0 of port 1
        self.dut.send_expect("flow destroy 1 rule 0", "Flow rule #0 destroyed")
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-other", ["3"], port_id=1)

        # flush rules of port 1
        self.dut.send_expect("flow flush 1", "testpmd> ")
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", ["1", "4", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)

        # Set all the queues to the rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 0 1 2 3 4 5 6 7 end / end",
            "created",
        )
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=0)

        # Set a wrong parameter: queue ID is 16
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 8 end / end",
            "Invalid argument",
        )

    def test_set_rss_types_rss_queue(self):
        """
        Set valid and invalid parameter.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=8 --txq=8 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create rss rules on port 0
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)
        self.send_check_100_packet_queue("ipv4-udp", "all", port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=1)

        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 0 2 7 end / end",
            "created",
        )
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-other", "0", port_id=0)
        self.send_check_100_packet_queue("ipv4-other", "all", port_id=1)
        self.send_check_100_packet_queue("ipv4-udp", ["0", "2", "7"], port_id=0)
        self.send_check_100_packet_queue("ipv4-udp", "0", port_id=1)

        # Create rss rules on port 1
        self.dut.send_expect(
            "flow create 1 ingress pattern end actions rss types end queues 1 4 7 end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / end actions rss types l2-payload end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / sctp / end actions rss types ipv6-sctp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / udp / end actions rss types ipv6-udp end queues end / end",
            "created",
        )
        # send the packets and verify the results
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        ptype_list2 = [
            "ipv4-udp",
            "ipv4-tcp",
            "ipv6-other",
            "ipv6-udp",
            "ipv6-sctp",
            "l2-payload",
        ]
        ptype_list3 = ["ipv4-other", "ipv4-frag", "ipv4-sctp", "ipv6-frag", "ipv6-tcp"]
        self.send_check_100_packet_queue("ipv4-udp", ["0", "2", "7"], port_id=0)
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        self.send_check_100_packet_queue(ptype_list2, ["1", "4", "7"], port_id=1)
        self.send_check_100_packet_queue(ptype_list3, "0", port_id=1)

        # Set a different RSS queue rule on port 1
        self.dut.send_expect(
            "flow create 1 ingress pattern end actions rss types end queues 3 end / end",
            "created",
        )
        self.send_check_100_packet_queue("ipv4-udp", ["0", "2", "7"], port_id=0)
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        self.send_check_100_packet_queue(ptype_list2, ["3"], port_id=1)
        self.send_check_100_packet_queue(ptype_list3, "0", port_id=1)

    def test_set_key_keylen(self):
        """
        Set key and key_len.
        """
        # Only supported by i40e
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        pkt1 = (
            "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=100, dport=200)/('X'*48)"
            % self.pf0_mac
        )
        pkt2 = (
            "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=100, dport=201)/('X'*48)"
            % self.pf0_mac
        )
        pkt3 = (
            "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.0')/UDP(sport=101, dport=201)/('X'*48)"
            % self.pf0_mac
        )
        pkt4 = (
            "Ether(dst='%s')/IP(src='0.0.0.0',dst='4.0.0.1')/UDP(sport=101, dport=201)/('X'*48)"
            % self.pf0_mac
        )
        pkt5 = (
            "Ether(dst='%s')/IP(src='0.0.0.1',dst='4.0.0.1')/UDP(sport=101, dport=201)/('X'*48)"
            % self.pf0_mac
        )
        pkts = [pkt1, pkt2, pkt3, pkt4, pkt5]

        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss rule
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        out1 = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ", 120)
        rss_queue = ["0", "1", "2", "3"]
        port0_list1 = self.send_and_check(pkts, rss_queue, port_id=0)
        port1_list1 = self.send_and_check(pkts, rss_queue, port_id=1)

        # Create a rss key rule on port 0
        key = "1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFFFFFFFF"
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end key %s / end"
            % key,
            "created",
        )
        out2 = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ", 120)
        port0_list2 = self.send_and_check(pkts, rss_queue, port_id=0)
        port1_list2 = self.send_and_check(pkts, rss_queue, port_id=1)

        self.verify(
            (key in out2) and (out1 != out2) and (port0_list1 != port0_list2),
            "the key setting doesn't take effect.",
        )

        # Create a rss key rule with truncating key_len on port 0
        key = "1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFFFFFFFF"
        key_len = "50"
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end key %s key_len %s / end"
            % (key, key_len),
            "created",
        )
        out3 = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ", 120)
        port0_list3 = self.send_and_check(pkts, rss_queue, port_id=0)
        port1_list3 = self.send_and_check(pkts, rss_queue, port_id=1)

        self.verify(
            (key in out2) and (out1 != out2) and (port0_list1 != port0_list2),
            "the key setting doesn't take effect.",
        )

        self.verify(
            (key not in out3)
            and (out3 == out1 and out1 != out2)
            and (port0_list3 == port0_list1 and port0_list1 != port0_list2),
            "the key setting doesn't take effect.",
        )

        # Create a rss rule with padding key_len on port 0
        key = "1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678901234567890FFFFFF"
        key_len = "52"
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end key %s key_len %s / end"
            % (key, key_len),
            "created",
        )
        out4 = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ", 120)
        port0_list4 = self.send_and_check(pkts, rss_queue, port_id=0)
        port1_list4 = self.send_and_check(pkts, rss_queue, port_id=1)

        self.verify(
            (key in out4)
            and (out4 != out1 != out2 != out3)
            and (port0_list4 != port0_list1 != port0_list2),
            "the key setting doesn't take effect.",
        )
        self.verify(
            port1_list1 == port1_list2 == port1_list3 == port1_list4,
            "the key setting on port 0 impact port 1.",
        )

        # Create a rss key rule on port 1
        key = "1234567890123456789012345678901234567890FFFFFFFFFFFF1234567890123456789012345678909876543210EEEEEEEEEEEE"
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end key %s / end"
            % key,
            "created",
        )
        out5 = self.dut.send_expect("show port 1 rss-hash key", "testpmd> ", 120)
        port0_list5 = self.send_and_check(pkts, rss_queue, port_id=0)
        port1_list5 = self.send_and_check(pkts, rss_queue, port_id=1)

        self.verify(
            (key in out5) and (out1 != out5) and (port1_list4 != port1_list5),
            "the key setting doesn't take effect.",
        )
        self.verify(
            port0_list5 == port0_list4, "the key setting on port 1 impact port 0."
        )

    def test_disable_rss_in_commandline(self):
        """
        Set RSS queue rule while disable RSS in command-line.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=8 --txq=8 --disable-rss --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=1)

        # enable ipv4-udp and ipv6-tcp RSS function type
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp / end actions rss types ipv6-tcp end queues end / end",
            "created",
        )

        ptype_list1 = ["ipv4-udp", "ipv6-tcp"]
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)
        ptype_list2 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)
        ptype_list3 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list3, "0", port_id=1)

        #  set queue 1, 4, 7 into RSS queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 1 4 7 end / end",
            "created",
        )
        ptype_list1 = ["ipv4-udp", "ipv6-tcp"]
        self.send_check_100_packet_queue(ptype_list1, ["1", "4", "7"], port_id=0)
        ptype_list2 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)
        ptype_list3 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list3, "0", port_id=1)

        # enable ipv4-udp and ipv6-other RSS function type on port 1
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 1 ingress pattern eth / ipv6 / end actions rss types ipv6-other end queues end / end",
            "created",
        )
        ptype_list1 = ["ipv4-udp", "ipv6-tcp"]
        self.send_check_100_packet_queue(ptype_list1, ["1", "4", "7"], port_id=0)
        ptype_list2 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)
        ptype_list3 = ["ipv4-udp", "ipv6-other"]
        self.send_check_100_packet_queue(ptype_list3, "all", port_id=1)
        ptype_list4 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list4, "0", port_id=1)

        self.dut.send_expect("flow flush 0", "testpmd> ")
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        ptype_list2 = ["ipv4-udp", "ipv6-other"]
        self.send_check_100_packet_queue(ptype_list2, "all", port_id=1)
        ptype_list3 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list3, "0", port_id=1)

        self.dut.send_expect("flow flush 1", "testpmd> ")
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
            "l2-payload",
        ]
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=1)

    def test_flow_director_rss_rule_combination(self):
        """
        Set RSS queue rule and flow director rule in meantime.
        flow directory filter is priority to RSS hash filter.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=8 --txq=8 --pkt-filter-mode=perfect"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Enable ipv4-udp type and Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 3 4 5 end / end",
            "created",
        )
        # send the packets and verify the results
        rss_queue = ["3", "4", "5"]
        self.send_and_check(self.pkt2, rss_queue, port_id=0)

        # Create a flow director rule
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 src is 10.0.0.1 dst is 192.168.0.2 / udp src is 50 dst is 50 / end actions queue index 1 / end",
            "created",
        )
        # send the packets and verify the results
        rss_queue = ["1"]
        self.send_and_check(self.pkt2, rss_queue, port_id=0)
        # There can't be more than one RSS queue rule existing.
        self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ")
        rss_queue = ["3", "4", "5"]
        self.send_and_check(self.pkt2, rss_queue, port_id=0)

    def test_queue_region_with_rte_flow_api(self):
        """
        Set RSS queue rule with queue region API.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=16 --txq=16 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 7 8 10 11 12 14 15 end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp / end actions rss types ipv4-tcp end queues end / end",
            "created",
        )
        # send the packets and verify the results
        rss_queue = ["7", "8", "10", "11", "12", "14", "15"]
        pkts = [self.prio_pkt1, self.prio_pkt2, self.prio_pkt3]
        queue_list = self.send_and_check(pkts, rss_queue, port_id=0)
        self.verify(
            queue_list[0] == queue_list[1] == queue_list[2],
            "the packet doesn't enter the expected RSS queue.",
        )

        # Create three queue regions.
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 7 8 end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x4000 / end actions rss queues 11 12 end / end",
            "created",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x6000 / end actions rss queues 15 end / end",
            "created",
        )
        # send the packets and verify the results
        rss_queue = ["7", "8"]
        queue1 = self.send_and_check(self.prio_pkt1, rss_queue, port_id=0)
        rss_queue = ["11", "12"]
        queue2 = self.send_and_check(self.prio_pkt2, rss_queue, port_id=0)
        rss_queue = ["15"]
        queue3 = self.send_and_check(self.prio_pkt3, rss_queue, port_id=0)

        # Destroy one queue region rule, all the rules become invalid.
        self.dut.send_expect("flow destroy 0 rule 3", "testpmd> ")
        rss_queue = ["7", "8", "10", "11", "12", "14", "15"]
        queue_list2 = self.send_and_check(pkts, rss_queue, port_id=0)
        self.verify(
            queue_list == queue_list2,
            "the packet doesn't enter the expected RSS queue.",
        )

    def test_queue_region_in_rte_flow_with_invalid_parameter(self):
        """
        Set RSS queue region rule with invalid parameter in rte_flow API.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=16 --txq=16 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 10 11 end / end",
            "error",
        )
        # Create a rss queue rule.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 8 10 11 12 15 end / end",
            "created",
        )
        # Set a queue region with invalid queue ID
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 8 9 end / end",
            "error",
        )
        # Set a queue region with discontinuous queue ID
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 8 10 end / end",
            "error",
        )
        # Set a queue region with invalid queue number
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x4000 / end actions rss queues 10 11 12 end / end",
            "error",
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern vlan tci is 0x2000 / end actions rss queues 10 11 end / end",
            "created",
        )

    def test_queue_region_with_rss_rule_combination(self):
        """
        Set RSS queue rule with old API, while setting RSS queue rule.
        The queue region is priority to RSS queue rule.
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=16 --txq=16 --port-topology=chained"
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp / end actions rss types ipv4-udp end queues end / end",
            "created",
            120,
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Set a queue region.
        self.dut.send_expect(
            "set port 0 queue-region region_id 0 queue_start_index 1 queue_num 1",
            "testpmd> ",
        )
        self.dut.send_expect(
            "set port 0 queue-region region_id 0 flowtype 31", "testpmd> "
        )
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        # send the packets and verify the results
        rss_queue = ["1"]
        self.send_and_check(self.pkt2, rss_queue, port_id=0)

        # Create a RSS queue rule.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types end queues 6 7 end / end",
            "testpmd> ",
        )
        # send the packets and verify the results
        rss_queue = ["1"]
        self.send_and_check(self.pkt2, rss_queue, port_id=0)

        # destroy the queue region.
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")
        # send the packets and verify the results
        rss_queue = ["6", "7"]
        self.send_and_check(self.pkt2, rss_queue, port_id=0)

    def test_disable_enable_rss_ixgbe_igb(self):
        """
        Disable and enable RSS.
        """
        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Show port default RSS functions
        self.dut.send_expect("show port 0 rss-hash", "ipv4 ipv6 ipv6-ex")
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
        ]
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)

        # Disable RSS hash function
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types none end / end",
            "created",
        )
        self.dut.send_expect("show port 0 rss-hash", "RSS disabled")
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)

        # Enable RSS hash function all
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types all end / end",
            "created",
        )
        self.dut.send_expect(
            "show port 0 rss-hash",
            "ipv4 ipv4-tcp ipv4-udp ipv6 ipv6-tcp ipv6-udp ipv6-ex ipv6-tcp-ex ipv6-udp-ex",
        )
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)

    def test_enable_ipv4_udp_rss_ixgbe_igb(self):
        """
        Enable IPv4-UDP RSS.
        """
        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.pmdout.start_testpmd(
            "%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained"
        )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Show port default RSS fucntions
        self.dut.send_expect("show port 0 rss-hash", "ipv4 ipv6 ipv6-ex")
        # enable ipv4-udp rss function
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end / end",
            "created",
        )
        self.dut.send_expect("show port 0 rss-hash", "ipv4-udp")
        # send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-udp", "all", port_id=0)
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
        ]
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)

    def test_rss_queue_rule_ixgbe_igb(self):
        """
        Set valid and invalid parameter.
        """
        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained"
            )
        else:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--rxq=8 --txq=8 --port-topology=chained"
            )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss queues 1 2 end / end",
                "created",
            )
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss queues 1 4 7 end / end",
                "created",
            )
        # send the packets and verify the results
        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
        ]
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.send_check_100_packet_queue(ptype_list1, ["1", "2"], port_id=0)
        else:
            self.send_check_100_packet_queue(ptype_list1, ["1", "4", "7"], port_id=0)

        # There can't be more than one RSS queue rule existing.
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 3 end / end", "error"
        )
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end queues 3 end / end",
            "error",
        )
        # Flush the rules and create a new RSS queue rule.
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types ipv4-udp end queues 3 end / end",
            "created",
        )
        # Send the packets and verify the results
        self.send_check_100_packet_queue("ipv4-udp", ["3"], port_id=0)
        ptype_list2 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
        ]
        self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)

        self.dut.send_expect("flow flush 0", "testpmd> ")

        # Set a wrong parameter: queue ID is 8
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss queues 8 end / end", "error"
        )
        # Set all the queues to the rule
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss queues 0 1 2 3 end / end",
                "created",
            )
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss queues 0 1 2 3 4 5 6 7 end / end",
                "created",
            )
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)

    def test_different_types_ixgbe_igb(self):
        """
        Set different types rss queue rules.
        """
        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--rxq=4 --txq=4 --port-topology=chained"
            )
        else:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--rxq=8 --txq=8 --port-topology=chained"
            )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types udp ipv4-tcp ipv6-sctp ipv4-other end queues 1 2 3 end / end",
                "created",
            )
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types udp ipv4-tcp ipv6-sctp ipv4-other end queues 1 4 7 end / end",
                "created",
            )
        self.dut.send_expect(
            "show port 0 rss-hash", "ipv4-tcp ipv4-udp ipv6-udp ipv6-udp-ex"
        )
        ptype_list1 = ["ipv4-udp", "ipv4-tcp", "ipv6-udp"]
        ptype_list2 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-tcp",
            "ipv6-sctp",
        ]

        # send the packets and verify the results
        if self.nic in ["cavium_a063", "cavium_a064"]:
            self.send_check_100_packet_queue(ptype_list1, ["1", "4", "7"], port_id=0)
        elif self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.send_check_100_packet_queue(ptype_list1, ["1", "2", "3"], port_id=0)
            self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)
        else:
            self.send_check_100_packet_queue(ptype_list1, ["1", "4", "7"], port_id=0)
            self.send_check_100_packet_queue(ptype_list2, "0", port_id=0)

        # Create different ptype rss rule.
        self.dut.send_expect("flow flush 0", "testpmd> ")

        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types ipv4 ipv6 end queues 1 3 end / end",
                "created",
            )
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types ipv4 ipv6 end queues 3 7 end / end",
                "created",
            )
        self.dut.send_expect("show port 0 rss-hash", "ipv4 ipv6")
        ptype_list3 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
        ]
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.send_check_100_packet_queue(ptype_list3, ["1", "3"], port_id=0)
        else:
            self.send_check_100_packet_queue(ptype_list3, ["3", "7"], port_id=0)

    def test_disable_rss_in_commandline_ixgbe_igb(self):
        """
        Set RSS queue rule while disable RSS in command-line.
        """
        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores,
                "--rxq=4 --txq=4 --disable-rss --port-topology=chained",
            )
        else:
            self.pmdout.start_testpmd(
                "%s" % self.cores,
                "--rxq=8 --txq=8 --disable-rss --port-topology=chained",
            )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        ptype_list1 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-udp",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-tcp",
            "ipv6-sctp",
        ]
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)

        # Create a rss queue rule
        self.dut.send_expect(
            "flow create 0 ingress pattern end actions rss types all end / end",
            "created",
        )
        self.send_check_100_packet_queue(ptype_list1, "all", port_id=0)

        # Delete the rule
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.send_check_100_packet_queue(ptype_list1, "0", port_id=0)

        # Create a rss queue rule
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types ipv6-tcp ipv4-udp end queues 1 2 3 end / end",
                "created",
            )
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types ipv6-tcp ipv4-udp end queues 5 6 7 end / end",
                "created",
            )
        self.dut.send_expect("show port 0 rss-hash", "ipv4-udp ipv6-tcp")

        # send the packets and verify the results
        ptype_list2 = ["ipv4-udp", "ipv6-tcp"]
        ptype_list3 = [
            "ipv4-other",
            "ipv4-frag",
            "ipv4-tcp",
            "ipv4-sctp",
            "ipv6-other",
            "ipv6-frag",
            "ipv6-udp",
            "ipv6-sctp",
        ]
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.send_check_100_packet_queue(ptype_list2, ["1", "2", "3"], port_id=0)
        else:
            self.send_check_100_packet_queue(ptype_list2, ["5", "6", "7"], port_id=0)
        self.send_check_100_packet_queue(ptype_list3, "0", port_id=0)

    def test_flow_director_rss_rule_combination_ixgbe_igb(self):
        """
        Set RSS queue rule and flow director rule in meantime.
        """
        self.verify(
            self.nic
            not in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_10G-10G_BASE_T_BC",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_25G-25G_SFP28",
                "I40E_10G-10G_BASE_T_X722",
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.pmdout.start_testpmd(
                "%s" % self.cores,
                "--rxq=4 --txq=4 --disable-rss --port-topology=chained",
            )
        else:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--rxq=8 --txq=8 --pkt-filter-mode=perfect"
            )
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # Create a rss queue rule
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types ipv4-udp end queues 2 3 end / end",
                "created",
            )
            self.send_and_check(self.pkt2, ["2", "3"], port_id=0)
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern end actions rss types ipv4-udp end queues 3 4 5 end / end",
                "created",
            )
            self.send_and_check(self.pkt2, ["3", "4", "5"], port_id=0)

        # Create a flow director rule
        if self.nic in [
            "IGB_1G-82580_COPPER",
            "IGB_1G-I350_COPPER",
            "IGB_1G-I210_COPPER",
            "IGC-I225_LM",
        ]:
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 proto is 17 / udp dst is 50 / end actions queue index 1 / end",
                "created",
            )
            self.send_and_check(self.pkt2, ["1"], port_id=0)
        else:
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 10.0.0.1 dst is 192.168.0.2 / udp src is 50 dst is 50 / end actions queue index 1 / end",
                "created",
            )
            self.send_and_check(self.pkt2, ["1"], port_id=0)
        # Delete the fdir rule
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ")
        if self.nic in ["IGC-I225_LM", "IGB_1G-I210_COPPER"]:
            self.send_and_check(self.pkt2, ["2", "3"], port_id=0)
        else:
            self.send_and_check(self.pkt2, ["3", "4", "5"], port_id=0)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_env()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.kill_all()
