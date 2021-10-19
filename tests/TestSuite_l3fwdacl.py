# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
DPDK Test suite
Layer-3 forwarding ACL test script.
"""

import re
import time

import framework.packet as packet
import framework.utils as utils
from framework.test_case import TestCase


class TestL3fwdacl(TestCase):

    all_ipv4_addresses = "0.0.0.0/0"
    all_ipv6_addresses = "0:0:0:0:0:0:0:0/0"
    all_ports = "0 : 65535"
    all_protocols = "0x00/0x00"

    core_list_configs = {
        "1S/1C/1T": {"config": "", "mask": "", "ports": []},
        "1S/1C/2T": {"config": "", "mask": "", "ports": []},
        "1S/2C/1T": {"config": "", "mask": "", "ports": []},
        "2S/1C/1T": {"config": "", "mask": "", "ports": []},
    }

    default_rule = {"Type": "ROUTE", "sIpAddr": "ALL", "dIpAddr": "ALL",
                    "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL",
                    "Port": "1"}

    acl_ipv4_rule_list = [
        {"Type": "ACL", "sIpAddr": "200.10.0.1/32", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "100.10.0.1/32",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "11 : 11", "dPort": "ALL", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "101 : 101", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "0x06/0xff", "Port": ""},
        {"Type": "ACL", "sIpAddr": "200.10.0.1/32", "dIpAddr": "100.10.0.1/32",
         "sPort": "11 : 11", "dPort": "101 : 101", "Protocol": "0x06/0xff",
         "Port": ""}
    ]

    acl_ipv6_rule_list = [
        {"Type": "ACL", "sIpAddr": "2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "11 : 11", "dPort": "ALL", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "101 : 101", "Protocol": "ALL", "Port": ""},
        {"Type": "ACL", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "0x06/0xff", "Port": ""},
        {"Type": "ACL", "sIpAddr": "2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128", "dIpAddr": "2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128",
         "sPort": "11 : 11", "dPort": "101 : 101", "Protocol": "0x06/0xff", "Port": ""},
    ]

    exact_rule_list_ipv4 = [
        {"Type": "ROUTE", "sIpAddr": "200.10.0.1/32",
         "dIpAddr": "100.10.0.1/32", "sPort": "11 : 11",
         "dPort": "101 : 101", "Protocol": "0x06/0xff", "Port": "0"},
        {"Type": "ROUTE", "sIpAddr": "200.20.0.1/32",
         "dIpAddr": "100.20.0.1/32", "sPort": "12 : 12",
         "dPort": "102 : 102", "Protocol": "0x06/0xff", "Port": "1"},
    ]

    exact_rule_list_ipv6 = [
        {"Type": "ROUTE", "sIpAddr": "2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128", "dIpAddr": "2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128",
         "sPort": "11 : 11", "dPort": "101 : 101", "Protocol": "0x06/0xff", "Port": "0"},
        {"Type": "ROUTE", "sIpAddr": "2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128", "dIpAddr": "2002:0db8:85a3:08d3:1319:8a2e:0370:7344/128",
         "sPort": "12 : 12", "dPort": "102 : 102", "Protocol": "0x06/0xff", "Port": "1"},
    ]

    lpm_rule_list_ipv4 = [
        {"Type": "ROUTE", "sIpAddr": "0.0.0.0/0", "dIpAddr": "1.1.1.0/24",
         "sPort": "0 : 65535", "dPort": "0 : 65535", "Protocol": "0x00/0x00",
         "Port": "0"},
        {"Type": "ROUTE", "sIpAddr": "0.0.0.0/0", "dIpAddr": "2.1.1.0/24",
         "sPort": "0 : 65535", "dPort": "0 : 65535", "Protocol": "0x00/0x00",
         "Port": "1"},
    ]

    lpm_rule_list_ipv6 = [
        {"Type": "ROUTE", "sIpAddr": "0:0:0:0:0:0:0:0/0", "dIpAddr": "1:1:1:1:1:1:0:0/96",
         "sPort": "0 : 65535", "dPort": "0 : 65535", "Protocol": "0x00/0x00", "Port": "0"},
        {"Type": "ROUTE", "sIpAddr": "0:0:0:0:0:0:0:0/0", "dIpAddr": "2:1:1:1:1:1:0:0/96",
         "sPort": "0 : 65535", "dPort": "0 : 65535", "Protocol": "0x00/0x00", "Port": "1"},
    ]

    scalar_rule_list_ipv4 = [
        {"Type": "ACL", "sIpAddr": "200.10.0.1/32", "dIpAddr": "100.10.0.1/32",
         "sPort": "11 : 11", "dPort": "101 : 101", "Protocol": "0x06/0xff",
         "Port": ""},
    ]

    scalar_rule_list_ipv6 = [
        {"Type": "ACL", "sIpAddr": "2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128", "dIpAddr": "2002:0db8:85a3:08d3:1319:8a2e:0370:7344/101",
         "sPort": "11 : 11", "dPort": "101 : 101", "Protocol": "0x06/0xff",
         "Port": ""},
    ]

    invalid_rule_ipv4_list = [
        {"Type": "ROUTE", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "12 : 11", "dPort": "ALL", "Protocol": "ALL", "Port": "0"},
        {"Type": "@R", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL", "Port": "0"},
        {"Type": "ROUTE", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "", "Port": ""},
    ]

    invalid_rule_ipv6_list = [
        {"Type": "ROUTE", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "12 : 11", "dPort": "ALL", "Protocol": "ALL", "Port": "0"},
        {"Type": "@R", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "ALL", "Port": "0"},
        {"Type": "ROUTE", "sIpAddr": "ALL", "dIpAddr": "ALL",
         "sPort": "ALL", "dPort": "ALL", "Protocol": "", "Port": ""},
    ]

    invalid_port_rule_ipv4 = {"Type": "ROUTE", "sIpAddr": "200.10.0.1/32",
                              "dIpAddr": "100.10.0.1/32", "sPort": "11 : 11",
                              "dPort": "101 : 101", "Protocol": "0x06/0xff",
                              "Port": "99"}

    invalid_port_rule_ipv6 = {"Type": "ACL", "sIpAddr": "2001:0db8:85a3:08d3:1319:8a2e:0370:7344/128", "dIpAddr": "2002:0db8:85a3:08d3:1319:8a2e:0370:7344/101",
                              "sPort": "11 : 11", "dPort": "101 : 101", "Protocol": "0x06/0xff", "Port": "99"}

    acl_ipv4_db = "/root/rule_ipv4.db"
    acl_ipv6_db = "/root/rule_ipv6.db"
    rule_format = "%s%s %s %s %s %s %s"
    default_core_config = "1S/4C/1T"

    # Utility methods and other non-test code.
    def start_l3fwdacl(self, scalar=False):

        extra_args = ''

        if scalar:
            extra_args = '--alg="scalar"'

        cmdline = '%s %s -- -p %s --config="(%d,0,2),(%d,0,3)" --rule_ipv4="%s" --rule_ipv6="%s" %s' % \
                  (self.app_l3fwd_acl_path, self.eal_para,
                   self.port_mask, self.dut_ports[0], self.dut_ports[1],
                   TestL3fwdacl.acl_ipv4_db,
                   TestL3fwdacl.acl_ipv6_db,
                   extra_args)

        out = self.dut.send_expect(cmdline, "L3FWD:", 30)

    def get_core_list(self):

        self.sock0ports = self.dut.get_ports(self.nic, socket=0)
        self.sock1ports = self.dut.get_ports(self.nic, socket=1)

        if len(self.sock0ports) > 0 and len(self.sock1ports) > 0:
            return self.dut.get_core_list("2S/4C/2T")
        else:
            return self.dut.get_core_list("1S/4C/1T")

    def rule_cfg_init(self, acl_ipv4_db, acl_ipv6_db):
        """
        initialize the acl rule file
        """
        if acl_ipv4_db:
            self.dut.send_expect("echo '' > %s" % acl_ipv4_db, "# ")
            self.dut.send_expect("echo 'R0.0.0.0/0 0.0.0.0/0 0 : 65535 0 : 65535 0x00/0x00 %s' >> %s" % (self.dut_ports[1], acl_ipv4_db), "# ")
        if acl_ipv6_db:
            self.dut.send_expect("echo '' > %s" % acl_ipv6_db, "# ")
            self.dut.send_expect("echo 'R0:0:0:0:0:0:0:0/0 0:0:0:0:0:0:0:0/0 0 : 65535 0 : 65535 0x00/0x00 %s' >> %s" % (self.dut_ports[1], acl_ipv6_db), "# ")

    def rule_cfg_delete(self, acl_ipv4_db, acl_ipv6_db):
        """
        delete the acle rule file
        """
        self.dut.send_expect("rm -rf  %s" % acl_ipv4_db, "# ")
        self.dut.send_expect("rm -rf  %s" % acl_ipv6_db, "# ")

    def create_ipv4_ip_not_match(self, ip_address):
        """
        generate ip not match rule ip
        """
        match = r"(\d+).(\d+).(\d+).(\d+)/(\d+)"
        m = re.search(match, ip_address)

        ip1 = int(m.group(1))
        ip2 = int(m.group(2))
        ip3 = int(m.group(3))
        ip4 = int(m.group(4))
        mask_len = int(m.group(5))

        ip = ip1 << 24 | ip2 << 16 | ip3 << 8 | ip4
        ip_diff = ((ip >> (32 - mask_len)) + 1) << (32 - mask_len)

        ip1 = (ip_diff & 0xff000000) >> 24
        ip2 = (ip_diff & 0x00ff0000) >> 16
        ip3 = (ip_diff & 0x0000ff00) >> 8
        ip4 = ip_diff & 0xff

        return "%d.%d.%d.%d/32" % (ip1, ip2, ip3, ip4)

    def create_ipv6_ip_not_match(self, ip_address):
        """
        generate ip not match rule ip
        """
        return "0:0:0:0:0:0:0:1/128"

    def create_port_not_match(self, port):
        """
        generate port number not match rule
        """
        return "0 : 0"

    def send_ipv4_packet_not_match(self, rule, tx_port, rx_port):
        """
        send a packet not match rule and return whether forwarded
        """
        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)
        if rule["sIpAddr"] != "ALL":
            rule["sIpAddr"] = self.create_ipv4_ip_not_match(rule["sIpAddr"])
        if rule["dIpAddr"] != "ALL":
            rule["dIpAddr"] = self.create_ipv4_ip_not_match(rule["dIpAddr"])
        if rule["sPort"] != "ALL":
            rule["sPort"] = self.create_port_not_match(rule["sPort"])
        if rule["dPort"] != "ALL":
            rule["dPort"] = self.create_port_not_match(rule["dPort"])
        if rule["Protocol"] != "ALL":
            if "6" in rule["Protocol"]:
                rule["Protocol"] = "0x11/0xff"
            else:
                rule["Protocol"] = "0x6/0xff"

        ethernet_str = self.create_ipv4_rule_string(rule, "Ether")

        dst_filter = {'layer': 'ether', 'config': {'dst': 'not ff:ff:ff:ff:ff:ff'}}
        filters = [dst_filter]
        inst = self.tester.tcpdump_sniff_packets(rx_interface, filters=filters)
        pkt = packet.Packet()
        pkt.append_pkt(ethernet_str)
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, timeout=30)
        out = self.remove_dhcp_from_revpackets(inst)
        return len(out)

    def send_ipv6_packet_not_match(self, rule, tx_port, rx_port):
        """
        send a packet not match rule and return whether forwardeid
        """
        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)
        if rule["sIpAddr"] != "ALL":
            rule["sIpAddr"] = self.create_ipv6_ip_not_match(rule["sIpAddr"])
        if rule["dIpAddr"] != "ALL":
            rule["dIpAddr"] = self.create_ipv6_ip_not_match(rule["dIpAddr"])
        if rule["sPort"] != "ALL":
            rule["sPort"] = self.create_port_not_match(rule["sPort"])
        if rule["dPort"] != "ALL":
            rule["dPort"] = self.create_port_not_match(rule["dPort"])
        if rule["Protocol"] != "ALL":
            if "6" in rule["Protocol"]:
                rule["Protocol"] = "0x11/0xff"
            else:
                rule["Protocol"] = "0x6/0xff"

        ethernet_str = self.create_ipv6_rule_string(rule, "Ether")

        fil = [{'layer': 'ether', 'config': {'dst': 'not ff:ff:ff:ff:ff:ff'}}]
        inst = self.tester.tcpdump_sniff_packets(rx_interface, filters=fil)
        pkt = packet.Packet()
        pkt.append_pkt(ethernet_str)
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, timeout=30)

        out = self.remove_dhcp_from_revpackets(inst)
        return len(out)

    def send_ipv4_packet_match(self, rule, tx_port, rx_port):
        """
        send a packet match rule and return whether forwarded
        """
        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)
        etherStr = self.create_ipv4_rule_string(rule, "Ether")

        dst_filter = {'layer': 'ether', 'config': {'dst': 'not ff:ff:ff:ff:ff:ff'}}
        filters = [dst_filter]
        inst = self.tester.tcpdump_sniff_packets(rx_interface, filters=filters)
        pkt = packet.Packet()
        pkt.append_pkt(etherStr)
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, timeout=30)
        out = self.remove_dhcp_from_revpackets(inst)
        return len(out)

    def send_ipv6_packet_match(self, rule, tx_port, rx_port):
        """
        send a packet match rule and return whether forwarded
        """
        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)
        etherStr = self.create_ipv6_rule_string(rule, "Ether")

        fil = [{'layer': 'ether', 'config': {'dst': 'not ff:ff:ff:ff:ff:ff'}}]
        inst = self.tester.tcpdump_sniff_packets(rx_interface, filters=fil)
        pkt = packet.Packet()
        pkt.append_pkt(etherStr)
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, timeout=30)

        out = self.remove_dhcp_from_revpackets(inst)
        return len(out)

    def remove_dhcp_from_revpackets(self, inst):
        p = self.tester.load_tcpdump_sniff_packets(inst,timeout=5)
        pkts = p.pktgen.pkts
        i = 0
        while len(pkts) != 0 and i <= len(pkts) - 1:
            if pkts[i].haslayer('DHCP'):
                pkts.remove(pkts[i])
                i = i - 1
            i = i + 1
        return pkts

    def create_ipv4_rule_string(self, rule, rule_type):
        """
        generate related string from rule
        """
        acl_promt = ""
        source_ip = ""
        source_ip_addr = ""
        destination_ip = ""
        destination_ip_addr = ""
        source_port = ""
        source_port_num = ""
        destination_port = ""
        destination_port_numer = ""
        protocol = ""
        protocol_str = ""

        if rule["Type"] == "ACL":
            acl_promt = "@"
        elif rule["Type"] == "ROUTE":
            acl_promt = "R"
        else:
            acl_promt = rule["Type"]

        if rule["sIpAddr"] == "ALL":
            source_ip = TestL3fwdacl.all_ipv4_addresses
            source_ip_addr = "200.10.0.1"
        else:
            source_ip = rule["sIpAddr"]
            source_ip_addr = rule["sIpAddr"].split('/')[0]

        if rule["dIpAddr"] == "ALL":
            destination_ip = TestL3fwdacl.all_ipv4_addresses
            destination_ip_addr = "100.10.0.1"
        else:
            destination_ip = rule["dIpAddr"]
            destination_ip_addr = rule["dIpAddr"].split('/')[0]

        if rule["sPort"] == "ALL":
            source_port = TestL3fwdacl.all_ports
            source_port_num = "11"
        else:
            source_port = rule["sPort"]
            source_port_num = rule["sPort"].split(' ')[0]

        if rule["dPort"] == "ALL":
            destination_port = TestL3fwdacl.all_ports
            destination_port_numer = "101"
        else:
            destination_port = rule["dPort"]
            destination_port_numer = rule["dPort"].split(' ')[0]

        if rule["Protocol"] == "ALL":
            protocol = TestL3fwdacl.all_protocols
            protocol_str = "UDP"
        else:
            protocol = rule["Protocol"]
            if "6" in rule["Protocol"]:
                protocol_str = "TCP"
            else:
                protocol_str = "UDP"

        port = rule["Port"]

        destination_mac = self.dut.get_mac_address(self.dut_ports[0])

        rule_str = TestL3fwdacl.rule_format % (acl_promt, source_ip,
                                               destination_ip,
                                               source_port,
                                               destination_port,
                                               protocol,
                                               port)

        ether_str = 'Ether(dst="%s")/IP(src="%s",dst="%s")/%s(sport=%s,dport=%s)' % \
                    (destination_mac, source_ip_addr, destination_ip_addr,
                     protocol_str, source_port_num, destination_port_numer)

        if rule_type == "DataBase":
            return rule_str
        elif rule_type == "Ether":
            return ether_str

    def create_ipv6_rule_string(self, rule, rule_type):
        """
        generate related string from rule
        """
        acl_promt = ""
        source_ip = ""
        source_ip_addr = ""
        destination_ip = ""
        destination_ip_addr = ""
        source_port = ""
        source_port_num = ""
        destination_port = ""
        destination_port_numer = ""
        protocol = ""
        protocol_str = ""

        if rule["Type"] == "ACL":
            acl_promt = "@"
        elif rule["Type"] == "ROUTE":
            acl_promt = "R"
        else:
            acl_promt = rule["Type"]

        if rule["sIpAddr"] == "ALL":
            source_ip = TestL3fwdacl.all_ipv6_addresses
            source_ip_addr = "200:0:0:0:0:0:0:1"
        else:
            source_ip = rule["sIpAddr"]
            source_ip_addr = rule["sIpAddr"].split('/')[0]

        if rule["dIpAddr"] == "ALL":
            destination_ip = TestL3fwdacl.all_ipv6_addresses
            destination_ip_addr = "100:0:0:0:0:0:0:1"
        else:
            destination_ip = rule["dIpAddr"]
            destination_ip_addr = rule["dIpAddr"].split('/')[0]

        if rule["sPort"] == "ALL":
            source_port = TestL3fwdacl.all_ports
            source_port_num = "11"
        else:
            source_port = rule["sPort"]
            source_port_num = rule["sPort"].split(' ')[0]

        if rule["dPort"] == "ALL":
            destination_port = TestL3fwdacl.all_ports
            destination_port_numer = "101"
        else:
            destination_port = rule["dPort"]
            destination_port_numer = rule["dPort"].split(' ')[0]

        if rule["Protocol"] == "ALL":
            protocol = TestL3fwdacl.all_protocols
            protocol_str = "UDP"
        else:
            protocol = rule["Protocol"]
            if "6" in rule["Protocol"]:
                protocol_str = "TCP"
            else:
                protocol_str = "UDP"

        port = rule["Port"]

        destination_mac = self.dut.get_mac_address(self.dut_ports[0])

        rule_str = TestL3fwdacl.rule_format % (acl_promt, source_ip,
                                               destination_ip,
                                               source_port,
                                               destination_port,
                                               protocol,
                                               port)

        ether_str = 'Ether(dst="%s")/IPv6(src="%s",dst="%s")/%s(sport=%s,dport=%s)' % \
                    (destination_mac, source_ip_addr, destination_ip_addr,
                     protocol_str, source_port_num, destination_port_numer)

        if rule_type == "DataBase":
            return rule_str
        elif rule_type == "Ether":
            return ether_str

    def create_acl_ipv4_db(self, rule_list):
        """
        create rule.db from rule_list
        """

        self.dut.send_expect("echo '' > %s" % TestL3fwdacl.acl_ipv4_db, "# ")
        for rule in rule_list:
            rule_str = self.create_ipv4_rule_string(rule, rule_type="DataBase")
            self.dut.send_expect("echo %s >> %s" % (rule_str,
                                                    TestL3fwdacl.acl_ipv4_db), "# ")

        return

    def create_acl_ipv6_db(self, rule_list):
        """
        create rule.db from rule_list
        """

        self.dut.send_expect("echo '' > %s" % TestL3fwdacl.acl_ipv6_db, "# ")
        for rule in rule_list:
            rule_str = self.create_ipv6_rule_string(rule, rule_type="DataBase")
            self.dut.send_expect("echo %s >> %s" % (rule_str,
                                                    TestL3fwdacl.acl_ipv6_db), "# ")

        return

    def basic_acl_ipv4_test(self, acl_rule):
        """
        Bbasic test for l3fwal-acl
        """
        rule_list = []
        rule_list.append(acl_rule)
        rule_list.append(TestL3fwdacl.default_rule)
        self.create_acl_ipv4_db(rule_list)

        self.start_l3fwdacl()

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv4_packet_match(acl_rule, tx_port, rx_port)
        out2 = self.send_ipv4_packet_not_match(acl_rule, tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)
        self.verify(out1 <=0, "Rx port receive unexpected packet")
        self.verify(out2 >= 1, "Rx port not receive expected packet")

    def basic_acl_ipv6_test(self, acl_rule):
        """
        Basic test for l3fwd-acl with ipv6 packets
        """
        rule_list = []
        rule_list.append(acl_rule)
        rule_list.append(TestL3fwdacl.default_rule)
        self.create_acl_ipv6_db(rule_list)

        self.start_l3fwdacl()

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv6_packet_match(acl_rule, tx_port, rx_port)
        out2 = self.send_ipv6_packet_not_match(acl_rule, tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)
        self.verify(out1 <= 0, "Rx port receive unexpected packet")
        self.verify(out2 >= 1, "Rx port not receive expected packet")

    def invalid_acl_ipv4_test(self, acl_rule):
        """
        Basic test for l3fwal-acl with invalid rule
        """

        rule_list = []
        rule_list.append(acl_rule)
        rule_list.append(TestL3fwdacl.default_rule)
        self.create_acl_ipv4_db(rule_list)

        cmdline = '%s %s -- -p %s --config="(%d,0,2),(%d,0,3)" --rule_ipv4="%s" --rule_ipv6="%s"' % \
                  (self.app_l3fwd_acl_path, self.eal_para,
                   self.port_mask, self.dut_ports[0], self.dut_ports[1],
                   TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        out = self.dut.send_expect(cmdline, "# ", 30)
        self.verify("rules error" in out, "l3fwd not detect invalid rule")
        self.dut.send_expect("^C", "#", 5)

    def invalid_acl_ipv6_test(self, acl_rule):
        """
        Basic test for l3fwal-acl with invalid rule
        """

        rule_list = []
        rule_list.append(acl_rule)
        rule_list.append(TestL3fwdacl.default_rule)
        self.create_acl_ipv6_db(rule_list)

        cmdline = '%s %s -- -p %s --config="(%d,0,2),(%d,0,3)" --rule_ipv4="%s" --rule_ipv6="%s"' % \
                  (self.app_l3fwd_acl_path, self.eal_para,
                   self.port_mask, self.dut_ports[0], self.dut_ports[1],
                   TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        out = self.dut.send_expect(cmdline, "# ", 30)
        self.verify("rules error" in out, "l3fwd not detect invalid rule")
        self.dut.send_expect("^C", "#", 5)

    def set_up_all(self):
        """
        Run at the start of each test suite.

        l3fwd Acl Prerequisites
        """

        # Based on h/w type, choose how many dut_ports to use
        ports = self.dut.get_ports(self.nic)

        # Verify that enough dut_ports are available
        self.verify(len(ports) >= 2, "Insufficient dut_ports for speed testing")

        # Verify that enough threads are available
        cores = self.get_core_list()
        self.verify(cores is not None, "Insufficient cores for speed testing")

        self.eal_para = self.dut.create_eal_parameters(cores=self.get_core_list())
        self.core_mask = utils.create_mask(cores)
        print("Core mask: %s" % self.core_mask)

        if self.dut.dpdk_version >= '20.11.0':
            self.eal_para += " --force-max-simd-bitwidth=0"

        valid_ports = [port for port in ports if self.tester.get_local_port(port) != -1]
        self.verify(
            len(valid_ports) >= 2, "Insufficient active dut_ports for speed testing")

        self.dut_ports = valid_ports
        print("Valid ports found in DUT: %s" % self.dut_ports)

        self.port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])
        print("Port mask: %s" % self.port_mask)

        TestL3fwdacl.default_rule["Port"] = self.dut_ports[1]

        # compile l3fwd-acl
        out = self.dut.build_dpdk_apps("examples/l3fwd-acl")
        self.app_l3fwd_acl_path = self.dut.apps_name['l3fwd-acl']
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def test_l3fwdacl_acl_rule(self):
        """
        l3fwd Access Control match ACL rule test
        """

        self.rule_cfg_init(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        for acl_rule in TestL3fwdacl.acl_ipv4_rule_list:
            self.basic_acl_ipv4_test(acl_rule)

        for acl_rule in TestL3fwdacl.acl_ipv6_rule_list:
            self.basic_acl_ipv6_test(acl_rule)

        self.rule_cfg_delete(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

    def test_l3fwdacl_exact_route(self):
        """
        l3fwd Access Control match Exact route rule test
        """

        self.rule_cfg_init(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        rule_list_ipv4 = []

        TestL3fwdacl.exact_rule_list_ipv4[0]["Port"] = self.dut_ports[0]
        TestL3fwdacl.exact_rule_list_ipv4[1]["Port"] = self.dut_ports[1]

        rule_list_ipv4.append(TestL3fwdacl.exact_rule_list_ipv4[0])
        rule_list_ipv4.append(TestL3fwdacl.exact_rule_list_ipv4[1])
        self.create_acl_ipv4_db(rule_list_ipv4)

        self.start_l3fwdacl()

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv4_packet_match(TestL3fwdacl.exact_rule_list_ipv4[0], tx_port, tx_port)
        out2 = self.send_ipv4_packet_match(TestL3fwdacl.exact_rule_list_ipv4[1], tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)

        self.verify(out1 >= 1, "Rx port0 not receive expected packet")
        self.verify(out2 >= 1, "Rx port1 not receive expected packet")

        rule_list_ipv6 = []

        TestL3fwdacl.exact_rule_list_ipv6[0]["Port"] = self.dut_ports[0]
        TestL3fwdacl.exact_rule_list_ipv6[1]["Port"] = self.dut_ports[1]

        rule_list_ipv6.append(TestL3fwdacl.exact_rule_list_ipv6[0])
        rule_list_ipv6.append(TestL3fwdacl.exact_rule_list_ipv6[1])
        self.create_acl_ipv6_db(rule_list_ipv6)

        self.start_l3fwdacl()

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv6_packet_match(TestL3fwdacl.exact_rule_list_ipv6[0], tx_port, tx_port)
        out2 = self.send_ipv6_packet_match(TestL3fwdacl.exact_rule_list_ipv6[1], tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)

        self.verify(out1 >= 1, "Rx port0 not receive expected packet")
        self.verify(out2 >= 1, "Rx port1 not receive expected packet")

        self.rule_cfg_delete(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

    def test_l3fwdacl_lpm_route(self):
        """
        l3fwd Access Control match Lpm route rule test
        """

        self.rule_cfg_init(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        rule_list_ipv4 = []

        TestL3fwdacl.lpm_rule_list_ipv4[0]["Port"] = self.dut_ports[0]
        TestL3fwdacl.lpm_rule_list_ipv4[1]["Port"] = self.dut_ports[1]

        rule_list_ipv4.append(TestL3fwdacl.lpm_rule_list_ipv4[0])
        rule_list_ipv4.append(TestL3fwdacl.lpm_rule_list_ipv4[1])
        self.create_acl_ipv4_db(rule_list_ipv4)

        self.start_l3fwdacl()

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv4_packet_match(TestL3fwdacl.lpm_rule_list_ipv4[0], tx_port, tx_port)
        out2 = self.send_ipv4_packet_match(TestL3fwdacl.lpm_rule_list_ipv4[1], tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)

        self.verify(out1 >= 1, "Rx port0 not receive expected packet")
        self.verify(out2 >= 1, "Rx port1 not receive expected packet")

        rule_list_ipv6 = []

        TestL3fwdacl.lpm_rule_list_ipv6[0]["Port"] = self.dut_ports[0]
        TestL3fwdacl.lpm_rule_list_ipv6[1]["Port"] = self.dut_ports[1]

        rule_list_ipv6.append(TestL3fwdacl.lpm_rule_list_ipv6[0])
        rule_list_ipv6.append(TestL3fwdacl.lpm_rule_list_ipv6[1])
        self.create_acl_ipv6_db(rule_list_ipv6)

        self.start_l3fwdacl()

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv6_packet_match(TestL3fwdacl.lpm_rule_list_ipv6[0], tx_port, tx_port)
        out2 = self.send_ipv6_packet_match(TestL3fwdacl.lpm_rule_list_ipv6[1], tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)

        self.verify(out1 >= 1, "Rx port0 not receive expected packet")
        self.verify(out2 >= 1, "Rx port1 not receive expected packet")

        self.rule_cfg_delete(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

    def test_l3fwdacl_scalar(self):
        """
        l3fwd Access Control match with Scalar function test
        """

        self.rule_cfg_init(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        rule_list_ipv4 = []
        rule_list_ipv4.append(TestL3fwdacl.scalar_rule_list_ipv4[0])
        rule_list_ipv4.append(TestL3fwdacl.default_rule)
        self.create_acl_ipv4_db(rule_list_ipv4)

        self.start_l3fwdacl(scalar=True)

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv4_packet_match(TestL3fwdacl.scalar_rule_list_ipv4[0], tx_port, rx_port)
        out2 = self.send_ipv4_packet_not_match(TestL3fwdacl.scalar_rule_list_ipv4[0], tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)

        self.verify(out1 <= 0, "Rx port received unexpected packet")
        self.verify(out2 >= 1, "Rx port not receive expected packet")

        rule_list_ipv6 = []
        rule_list_ipv6.append(TestL3fwdacl.scalar_rule_list_ipv6[0])
        rule_list_ipv6.append(TestL3fwdacl.default_rule)
        self.create_acl_ipv6_db(rule_list_ipv6)

        self.start_l3fwdacl(scalar=True)

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        out1 = self.send_ipv6_packet_match(TestL3fwdacl.scalar_rule_list_ipv6[0], tx_port, rx_port)
        out2 = self.send_ipv6_packet_not_match(TestL3fwdacl.scalar_rule_list_ipv6[0], tx_port, rx_port)

        self.dut.send_expect("^C", "#", 20)

        self.verify(out1 <= 0, "Rx port received unexpected packet")
        self.verify(out2 >= 1, "Rx port not receive expected packet")

        self.rule_cfg_delete(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

    def test_l3fwdacl_invalid(self):
        """
        l3fwd Access Control handle Invalid rule test
        """

        self.rule_cfg_init(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        for acl_rule in TestL3fwdacl.invalid_rule_ipv4_list:
            self.invalid_acl_ipv4_test(acl_rule)

        for acl_rule in TestL3fwdacl.invalid_rule_ipv6_list:
            self.invalid_acl_ipv6_test(acl_rule)

        rule_list_ipv4 = []
        rule_list_ipv4.append(TestL3fwdacl.invalid_port_rule_ipv4)
        self.create_acl_ipv4_db(rule_list_ipv4)

        cmdline = '%s %s -- -p %s --config="(%d,0,2),(%d,0,3)" --rule_ipv4="%s" --rule_ipv6="%s" --alg="scalar"' % \
                  (self.app_l3fwd_acl_path, self.eal_para,
                   self.port_mask, self.dut_ports[0], self.dut_ports[1],
                   TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        out = self.dut.send_expect(cmdline, "# ", 30)
        self.verify("fwd number illegal" in out, "l3fwd not detect invalid port")

        rule_list_ipv6 = []
        rule_list_ipv6.append(TestL3fwdacl.invalid_port_rule_ipv6)
        self.create_acl_ipv6_db(rule_list_ipv6)

        cmdline = '%s %s -- -p %s --config="(%d,0,2),(%d,0,3)" --rule_ipv4="%s" --rule_ipv6="%s" --alg="scalar"' % \
                  (self.app_l3fwd_acl_path, self.eal_para,
                   self.port_mask, self.dut_ports[0], self.dut_ports[1],
                   TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

        out = self.dut.send_expect(cmdline, "# ", 30)
        self.verify("fwd number illegal" in out, "l3fwd not detect invalid port")

        self.rule_cfg_delete(TestL3fwdacl.acl_ipv4_db, TestL3fwdacl.acl_ipv6_db)

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
