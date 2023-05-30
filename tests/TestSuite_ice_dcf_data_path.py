# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestICEDCFDataPath(TestCase):
    vf_mac = "D2:6B:4C:EB:1C:26"
    wrong_mac = "68:05:CA:8D:ED:A8"

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.used_dut_port = self.dut_ports[0]
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        self.dut_intf0 = self.dut.ports_info[self.used_dut_port]["intf"]
        self.tester_intf0 = self.tester.get_interface(self.tester.get_local_port(0))
        # Generate 1 trust VF on 1 PF, and request 1 DCF on the trust VF
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 4, self.kdriver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.dut_ports[0]]["vfs_port"]
        self.used_vf_pci = self.sriov_vfs_port_0[0].pci
        # config vf trust on and vf mac value
        self.dut.send_expect("ip link set %s vf 0 trust on" % self.dut_intf0, "#")
        self.dut.send_expect(
            "ip link set {} vf 0 mac {}".format(self.dut_intf0, self.vf_mac), "#"
        )
        self.sriov_vfs_port_0[0].bind_driver(self.vf_driver)
        self.pmd_output = PmdOutput(self.dut)
        self.pkt = Packet()

    def set_up(self):
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param="--txq=4 --rxq=4",
            prefix="vf",
            ports=[self.used_vf_pci],
            port_options={self.used_vf_pci: "cap=dcf"},
        )

    def send_packets(self, packets, tx_port, count=1):
        self.pkt.update_pkt(packets)
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port, count=count)

    def send_pkts_getouput(self, pkts, tx_port, count=1, status=False):
        # Get the DCF package information
        p = re.compile("RSS hash=(\w+)")
        self.send_packets(pkts, tx_port=tx_port, count=count)
        time.sleep(0.5)
        if status:
            out = self.pmd_output.get_output()
        else:
            # Get the DCF package rss hash value
            output = self.pmd_output.get_output()
            out = p.findall(output)
        return out

    def test_dcf_macfwd(self):
        """
        Test Case: Launch DCF and do macfwd
        """
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("start")
        inst = self.tester.tcpdump_sniff_packets(self.tester_intf0)
        pkts_cmd = 'Ether(dst="{}", src="00:11:22:33:44:55")/IP(src="192.168.1.1",dst="192.168.1.3")/Raw("x"*64)'.format(
            self.vf_mac
        )
        self.send_packets(pkts_cmd, self.tester_intf0, count=100)
        time.sleep(2)
        p = self.tester.load_tcpdump_sniff_packets(inst)
        self.verify(
            len(p) == 100, "send 100 packets received %d packets, not match" % len(p)
        )

    def test_default_rss_l3(self):
        """
        Test Case: Check default rss for L3
        """
        pkt_list1 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.3") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.3",dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
        ]
        pkt_list2 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::12") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::21", dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
        ]
        pkt_list3 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.1", dst="192.168.1.3") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.3", dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="11:22:33:44:55:77") / IP(src="1.1.1.2", dst="2.2.2.1") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="11:22:33:44:55:77") / IPv6(src="::11", dst="::22") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / Raw("x" * 64)'
            % self.vf_mac,
        ]
        pkt_list4 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::22",dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::22",dst="::12") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::21",dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="11:22:33:44:55:77") / IP(src="1.1.1.2",dst="2.2.2.1") / GRE() / IPv6(src="::22",dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="11:22:33:44:55:77") / IPv6(src="::33", dst="::44") / GRE() / IPv6(src="::22", dst="::11") / Raw("x" * 64)'
            % self.vf_mac,
        ]

        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        out1 = self.send_pkts_getouput(pkt_list1, self.tester_intf0)
        self.verify(
            out1[0] == out1[3] and out1[0] != out1[1] != out1[2],
            "ipv4 rss hash value test failed",
        )
        out2 = self.send_pkts_getouput(pkt_list2, self.tester_intf0)
        self.verify(
            out2[0] == out2[3] and out2[0] != out2[1] != out2[2],
            "ipv6 rss hash value test failed",
        )
        out3 = self.send_pkts_getouput(pkt_list3, self.tester_intf0)
        self.verify(
            out3[0] == out3[3] == out3[4] and out3[0] != out3[1] != out3[2],
            "inner ipv4 rss hash value test failed",
        )
        out4 = self.send_pkts_getouput(pkt_list4, self.tester_intf0)
        self.verify(
            out4[0] == out4[3] == out4[4] and out4[0] != out4[1] != out4[2],
            "inner ipv6 rss hash value test failed",
        )

    def test_default_rss_l4(self):
        """
        Test Case: Check default rss for L4
        """
        pkt_list1 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.2") / UDP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.3") / UDP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.3",dst="192.168.1.2") / UDP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.2") / UDP(sport=1235,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="192.168.1.1",dst="192.168.1.2") / UDP(sport=1234,dport=5679) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:22:33:44:55:77") / IP(src="192.168.1.1",dst="192.168.1.2") / TCP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
        ]
        pkt_list2 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::11") / UDP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::12") / UDP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::21", dst="::11") / UDP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::11") / UDP(sport=1235,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IPv6(src="::22", dst="::11") / UDP(sport=1234,dport=5679) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="11:22:33:44:55:77") / IPv6(src="::22", dst="::11") / TCP(sport=1234,dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
        ]
        pkt_list3 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / UDP(sport=22, dport=23) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.1", dst="192.168.1.3") / UDP(sport=22, dport=23) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.3", dst="192.168.1.2") / UDP(sport=22, dport=23) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / UDP(sport=21, dport=23) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1", dst="2.2.2.2") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / UDP(sport=22, dport=24) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:22:33:44:55:77") / IP(src="1.1.1.2", dst="2.2.2.1") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / UDP(sport=22, dport=23) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:22:33:44:55:77") / IPv6(src="::11", dst="::22") / GRE() / IP(src="192.168.1.1", dst="192.168.1.2") / TCP(sport=22, dport=23) / Raw("x" * 64)'
            % self.vf_mac,
        ]
        pkt_list4 = [
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::22",dst="::11") / UDP(sport=1234, dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::22",dst="::12") / UDP(sport=1234, dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::21",dst="::11") / UDP(sport=1234, dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::22",dst="::11") / UDP(sport=1235, dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:11:22:33:44:55") / IP(src="1.1.1.1",dst="2.2.2.2") / GRE() / IPv6(src="::22",dst="::11") / UDP(sport=1234, dport=5679) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:22:33:44:55:77") / IP(src="1.1.1.2",dst="2.2.2.1") / GRE() / IPv6(src="::22",dst="::11") / UDP(sport=1234, dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
            'Ether(dst="%s", src="00:22:33:44:55:77") / IPv6(src="::33", dst="::44") / GRE() / IPv6(src="::22", dst="::11") / UDP(sport=1234, dport=5678) / Raw("x" * 64)'
            % self.vf_mac,
        ]

        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        out1 = self.send_pkts_getouput(pkt_list1, self.tester_intf0)
        self.verify(
            out1[0] == out1[5] and out1[0] != out1[1] != out1[2] != out1[3] != out1[4],
            "ipv4 rss hash value test failed",
        )
        out2 = self.send_pkts_getouput(pkt_list2, self.tester_intf0)
        self.verify(
            out2[0] == out2[5] and out2[0] != out2[1] != out2[2] != out2[3] != out2[4],
            "ipv6 rss hash value test failed",
        )
        out3 = self.send_pkts_getouput(pkt_list3, self.tester_intf0)
        self.verify(
            out3[0] == out3[6]
            and out3[0] != out3[1] != out3[2] != out3[3] != out3[4] != out3[5],
            "inner ipv4 rss hash value test failed",
        )
        out4 = self.send_pkts_getouput(pkt_list4, self.tester_intf0)
        self.verify(
            out4[0] == out4[6]
            and out4[0] != out4[1] != out4[2] != out4[3] != out4[4] != out4[5],
            "inner ipv6 rss hash value test failed",
        )

    def test_create_rule_with_vf_action(self):
        """
        Test Case: Create rule with to original VF action
        """
        pkt = (
            'Ether(dst="%s")/IPv6(src="CDCD:910A:2222:5498:8475:1111:3900:1518", dst="CDCD:910A:2222:5498:8475:1111:3900:2020",tc=3)/TCP(sport=25,dport=23)/("X"*480)'
            % self.wrong_mac
        )
        rule = (
            "flow create 0 ingress pattern eth dst is %s / ipv6 dst is CDCD:910A:2222:5498:8475:1111:3900:2020 tc is 3 / tcp src is 25 dst is 23 / end actions port_representor port_id 0 / end"
            % self.wrong_mac
        )

        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set promisc all off")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        out = self.send_pkts_getouput(pkt, self.tester_intf0, status=True)
        self.verify(self.wrong_mac not in out, "The wrong mac packet was received")
        self.pmd_output.execute_cmd(rule, "created")
        out = self.send_pkts_getouput(pkt, self.tester_intf0, status=True)
        self.verify(self.wrong_mac in out, "The wrong mac packet not received")
        self.pmd_output.execute_cmd("flow destroy 0 rule 0", "destroyed")
        out = self.send_pkts_getouput(pkt, self.tester_intf0, status=True)
        self.verify(self.wrong_mac not in out, "The wrong mac packet was received")

    def tear_down(self):
        self.pmd_output.execute_cmd("quit", "#")

    def tear_down_all(self):
        self.dut.kill_all()
        self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
