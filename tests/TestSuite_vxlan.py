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

"""
DPDK Test suite.

Test VXLAN behaviour in DPDK.

"""

import os
import re
import string
import time
from random import randint

from scapy.config import conf
from scapy.layers.inet import IP, TCP, UDP, Ether
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import Dot1Q
from scapy.layers.sctp import SCTP, SCTPChunkData
from scapy.layers.vxlan import VXLAN
from scapy.route import *
from scapy.sendrecv import sniff
from scapy.utils import rdpcap, wrpcap

import framework.packet as packet
import framework.utils as utils
from framework.packet import IncreaseIP, IncreaseIPv6
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import FOLDERS, HEADER_SIZE
from framework.test_case import TestCase

#
#
# Test class.
#

VXLAN_PORT = 4789
PACKET_LEN = 128
MAX_TXQ_RXQ = 4
BIDIRECT = True


class VxlanTestConfig(object):

    """
    Module for config/create/transmit vxlan packet
    """

    def __init__(self, test_case, **kwargs):
        self.test_case = test_case
        self.init()
        for name in kwargs:
            setattr(self, name, kwargs[name])
        self.pkt_obj = packet.Packet()

    def init(self):
        self.packets_config()

    def packets_config(self):
        """
        Default vxlan packet format
        """
        self.pcap_file = packet.TMP_PATH + "vxlan.pcap"
        self.capture_file = packet.TMP_PATH + "vxlan_capture.pcap"
        self.outer_mac_src = "00:00:10:00:00:00"
        self.outer_mac_dst = "11:22:33:44:55:66"
        self.outer_vlan = "N/A"
        self.outer_ip_src = "192.168.1.1"
        self.outer_ip_dst = "192.168.1.2"
        self.outer_ip_invalid = 0
        self.outer_ip6_src = "N/A"
        self.outer_ip6_dst = "N/A"
        self.outer_ip6_invalid = 0
        self.outer_udp_src = 63
        self.outer_udp_dst = VXLAN_PORT
        self.outer_udp_invalid = 0
        self.vni = 1
        self.inner_mac_src = "00:00:20:00:00:00"
        self.inner_mac_dst = "00:00:20:00:00:01"
        self.inner_vlan = "N/A"
        self.inner_ip_src = "192.168.2.1"
        self.inner_ip_dst = "192.168.2.2"
        self.inner_ip_invalid = 0
        self.inner_ip6_src = "N/A"
        self.inner_ip6_dst = "N/A"
        self.inner_ip6_invalid = 0
        self.payload_size = 18
        self.inner_l4_type = "UDP"
        self.inner_l4_invalid = 0

    def packet_type(self):
        """
        Return vxlan packet type
        """
        if self.outer_udp_dst != VXLAN_PORT:
            if self.outer_ip6_src != "N/A":
                return "L3_IPV6_EXT_UNKNOWN"
            else:
                return "L3_IPV4_EXT_UNKNOWN"
        else:
            if self.inner_ip6_src != "N/A":
                return "L3_IPV6_EXT_UNKNOWN"
            else:
                return "L3_IPV4_EXT_UNKNOWN"

    def create_pcap(self):
        """
        Create pcap file and copy it to tester if configured
        Return scapy packet object for later usage
        """
        if self.inner_l4_type == "SCTP":
            self.inner_payload = SCTPChunkData(data="X" * 16)
        else:
            self.inner_payload = "X" * self.payload_size

        if self.inner_l4_type == "TCP":
            l4_pro = TCP()
        elif self.inner_l4_type == "SCTP":
            l4_pro = SCTP()
        else:
            l4_pro = UDP()

        if self.inner_ip6_src != "N/A":
            inner_l3 = IPv6()
        else:
            inner_l3 = IP()

        if self.inner_vlan != "N/A":
            inner = Ether() / Dot1Q() / inner_l3 / l4_pro / self.inner_payload
            inner[Dot1Q].vlan = self.inner_vlan
        else:
            inner = Ether() / inner_l3 / l4_pro / self.inner_payload

        if self.inner_ip6_src != "N/A":
            inner[inner_l3.name].src = self.inner_ip6_src
            inner[inner_l3.name].dst = self.inner_ip6_dst
        else:
            inner[inner_l3.name].src = self.inner_ip_src
            inner[inner_l3.name].dst = self.inner_ip_dst

        if self.inner_ip_invalid == 1:
            inner[inner_l3.name].chksum = 0

        # when udp checksum is 0, will skip checksum
        if self.inner_l4_invalid == 1:
            if self.inner_l4_type == "SCTP":
                inner[SCTP].chksum = 0
            else:
                inner[self.inner_l4_type].chksum = 1

        inner[Ether].src = self.inner_mac_src
        inner[Ether].dst = self.inner_mac_dst

        if self.outer_ip6_src != "N/A":
            outer_l3 = IPv6()
        else:
            outer_l3 = IP()

        if self.outer_vlan != "N/A":
            outer = Ether() / Dot1Q() / outer_l3 / UDP()
            outer[Dot1Q].vlan = self.outer_vlan
        else:
            outer = Ether() / outer_l3 / UDP()

        outer[Ether].src = self.outer_mac_src
        outer[Ether].dst = self.outer_mac_dst

        if self.outer_ip6_src != "N/A":
            outer[outer_l3.name].src = self.outer_ip6_src
            outer[outer_l3.name].dst = self.outer_ip6_dst
        else:
            outer[outer_l3.name].src = self.outer_ip_src
            outer[outer_l3.name].dst = self.outer_ip_dst

        outer[UDP].sport = self.outer_udp_src
        outer[UDP].dport = self.outer_udp_dst

        if self.outer_ip_invalid == 1:
            outer[outer_l3.name].chksum = 0
        # when udp checksum is 0, will skip checksum
        if self.outer_udp_invalid == 1:
            outer[UDP].chksum = 1

        if self.outer_udp_dst == VXLAN_PORT:
            self.pkt = outer / VXLAN(vni=self.vni) / inner
        else:
            self.pkt = outer / ("X" * self.payload_size)

        wrpcap(self.pcap_file, self.pkt)

        return self.pkt

    def get_chksums(self, pkt=None):
        """
        get chksum values of Outer and Inner packet L3&L4
        Skip outer udp for it will be calculated by software
        """
        chk_sums = {}
        if pkt is None:
            pkt = rdpcap(self.pcap_file)
        else:
            pkt = pkt.pktgen.pkt

        time.sleep(1)
        if pkt[0].guess_payload_class(pkt[0]).name == "802.1Q":
            payload = pkt[0][Dot1Q]
        else:
            payload = pkt[0]

        if payload.guess_payload_class(payload).name == "IP":
            chk_sums["outer_ip"] = hex(payload[IP].chksum)

        if pkt[0].haslayer("VXLAN") == 1:
            inner = pkt[0]["VXLAN"]
            if inner.haslayer(IP) == 1:
                chk_sums["inner_ip"] = hex(inner[IP].chksum)
                if inner[IP].proto == 6:
                    chk_sums["inner_tcp"] = hex(inner[TCP].chksum)
                if inner[IP].proto == 17:
                    chk_sums["inner_udp"] = hex(inner[UDP].chksum)
                if inner[IP].proto == 132:
                    chk_sums["inner_sctp"] = hex(inner[SCTP].chksum)
            elif inner.haslayer(IPv6) == 1:
                if inner[IPv6].nh == 6:
                    chk_sums["inner_tcp"] = hex(inner[TCP].chksum)
                if inner[IPv6].nh == 17:
                    chk_sums["inner_udp"] = hex(inner[UDP].chksum)
                # scapy can not get sctp checksum, so extracted manually
                if inner[IPv6].nh == 59:
                    load = str(inner[IPv6].payload)
                    chk_sums["inner_sctp"] = hex(
                        (ord(load[8]) << 24)
                        | (ord(load[9]) << 16)
                        | (ord(load[10]) << 8)
                        | (ord(load[11]))
                    )

        return chk_sums

    def send_pcap(self, iface=""):
        """
        Send vxlan pcap file by iface
        """
        del self.pkt_obj.pktgen.pkts[:]
        self.pkt_obj.pktgen.assign_pkt(self.pkt)
        self.pkt_obj.pktgen.update_pkts()
        self.pkt_obj.send_pkt(crb=self.test_case.tester, tx_port=iface)

    def pcap_len(self):
        """
        Return length of pcap packet, will plus 4 bytes crc
        """
        # add four bytes crc
        return len(self.pkt) + 4


class TestVxlan(TestCase):
    def set_up_all(self):
        """
        vxlan Prerequisites
        """
        # this feature only enable in Intel® Ethernet 700 Series now
        if self.nic in [
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_25G-25G_SFP28",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_X722",
            "I40E_10G-10G_BASE_T_BC",
        ]:
            self.compile_switch = "CONFIG_RTE_LIBRTE_I40E_INC_VECTOR"
        elif self.nic in ["IXGBE_10G-X550T", "IXGBE_10G-X550EM_X_10G_T"]:
            self.compile_switch = "CONFIG_RTE_IXGBE_INC_VECTOR"
        elif self.nic in ["ICE_25G-E810C_SFP", "ICE_100G-E810C_QSFP"]:
            print("Intel® Ethernet 700 Series support default none VECTOR")
        else:
            self.verify(False, "%s not support this vxlan" % self.nic)
        # Based on h/w type, choose how many ports to use
        ports = self.dut.get_ports()

        # Verify that enough ports are available
        self.verify(len(ports) >= 2, "Insufficient ports for testing")
        global valports
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]

        self.portMask = utils.create_mask(valports[:2])

        # Verify that enough threads are available
        netdev = self.dut.ports_info[ports[0]]["port"]
        self.ports_socket = netdev.socket

        # start testpmd
        self.pmdout = PmdOutput(self.dut)

        # init port config
        self.dut_port = valports[0]
        self.dut_port_mac = self.dut.get_mac_address(self.dut_port)
        tester_port = self.tester.get_local_port(self.dut_port)
        self.tester_iface = self.tester.get_interface(tester_port)
        self.recv_port = valports[1]
        tester_recv_port = self.tester.get_local_port(self.recv_port)
        self.recv_iface = self.tester.get_interface(tester_recv_port)

        # invalid parameter
        self.invalid_mac = "00:00:00:00:01"
        self.invalid_ip = "192.168.1.256"
        self.invalid_vlan = 4097
        self.invalid_queue = 64
        self.path = self.dut.apps_name["test-pmd"]

        # vxlan payload length for performance test
        # inner packet not contain crc, should need add four
        self.vxlan_payload = (
            PACKET_LEN
            - HEADER_SIZE["eth"]
            - HEADER_SIZE["ip"]
            - HEADER_SIZE["udp"]
            - HEADER_SIZE["vxlan"]
            - HEADER_SIZE["eth"]
            - HEADER_SIZE["ip"]
            - HEADER_SIZE["udp"]
            + 4
        )

        self.cal_type = [
            {
                "Type": "SOFTWARE ALL",
                "csum": [],
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Type": "HW L4",
                "csum": ["udp"],
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Type": "HW L3&L4",
                "csum": ["ip", "udp", "outer-ip"],
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Type": "SOFTWARE ALL",
                "csum": [],
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Type": "HW L4",
                "csum": ["udp"],
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Type": "HW L3&L4",
                "csum": ["ip", "udp", "outer-ip"],
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
        ]

        self.chksum_header = ["Calculate Type"]
        self.chksum_header.append("Queues")
        self.chksum_header.append("Mpps")
        self.chksum_header.append("% linerate")

        # tunnel filter performance test
        self.default_vlan = 1
        self.tunnel_multiqueue = 2
        self.tunnel_header = ["Packet", "Filter", "Queue", "Mpps", "% linerate"]
        self.tunnel_perf = [
            {
                "Packet": "Normal",
                "tunnel_filter": "None",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "None",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac-ivlan",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac-ivlan-tenid",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac-tenid",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "omac-imac-tenid",
                "recvqueue": "Single",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "None",
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac-ivlan",
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac-ivlan-tenid",
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac-tenid",
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "imac",
                "recvqueue": "Multi",
                "Mpps": {},
                "pct": {},
            },
            {
                "Packet": "VXLAN",
                "tunnel_filter": "omac-imac-tenid",
                "recvqueue": "Multi",
            },
        ]

        self.pktgen_helper = PacketGeneratorHelper()

    def set_fields(self):
        fields_config = {
            "ip": {
                "src": {"action": "random"},
                "dst": {"action": "random"},
            },
        }
        return fields_config

    def suite_measure_throughput(self, tgen_input, use_vm=False):
        vm_config = self.set_fields()
        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, 100, vm_config if use_vm else None, self.tester.pktgen
        )
        result = self.tester.pktgen.measure_throughput(stream_ids=streams)

        return result

    def perf_tunnel_filter_set_rule(self, rule_config):
        rule_list = {
            # check inner mac + inner vlan filter can work
            "imac-ivlan": f'flow create {rule_config.get("dut_port")} ingress pattern eth / '
            f'ipv4 / udp / vxlan / eth dst is {rule_config.get("inner_mac_dst")} / '
            f'vlan tci is {rule_config.get("inner_vlan")} / end actions pf / '
            f'queue index {rule_config.get("queue")} / end',
            # check inner mac + inner vlan + tunnel id filter can work
            "imac-ivlan-tenid": f'flow create {rule_config.get("dut_port")} ingress pattern eth / '
            f'ipv4 / udp / vxlan vni is {rule_config.get("vni")} / '
            f'eth dst is {rule_config.get("inner_mac_dst")} / '
            f'vlan tci is {rule_config.get("inner_vlan")} / '
            f'end actions pf / queue index {rule_config.get("queue")} / end',
            # check inner mac + tunnel id filter can work
            "imac-tenid": f'flow create {rule_config.get("dut_port")} ingress pattern eth / '
            f'ipv4 / udp / vxlan vni is {rule_config.get("vni")} / '
            f'eth dst is {rule_config.get("inner_mac_dst")} / end actions pf / '
            f'queue index {rule_config.get("queue")} / end',
            # check inner mac filter can work
            "imac": f'flow create {rule_config.get("dut_port")} ingress pattern eth / '
            f'ipv4 / udp / vxlan / eth dst is {rule_config.get("inner_mac_dst")} / end actions pf / '
            f'queue index {rule_config.get("queue")} / end',
            # check outer mac + inner mac + tunnel id filter can work
            "omac-imac-tenid": f'flow create {rule_config.get("dut_port")} ingress pattern '
            f'eth dst is {rule_config.get("outer_mac_dst")} / '
            f'ipv4 / udp / vxlan vni is {rule_config.get("vni")} / '
            f'eth dst is {rule_config.get("inner_mac_dst")} / '
            f'end actions pf / queue index {rule_config.get("queue")} / end',
        }
        rule = rule_list.get(rule_config.get("tun_filter"))
        if not rule:
            msg = "not support format"
            self.logger.error(msg)
            return
        out = self.dut.send_expect(rule, "testpmd>", 3)
        pat = "Flow rule #\d+ created"
        self.verify(re.findall(pat, out, re.M), "Flow rule create failed")

    def send_and_detect(self, **kwargs):
        """
        send vxlan packet and check whether testpmd detect the correct
        packet type
        """
        arg_str = ""
        for arg in kwargs:
            arg_str += "[%s = %s]" % (arg, kwargs[arg])

        # create pcap file with supplied arguments
        self.logger.info("send vxlan pkts %s" % arg_str)
        config = VxlanTestConfig(self, **kwargs)
        # now cloud filter will default enable L2 mac filter, so dst mac must
        # be same
        config.outer_mac_dst = self.dut_port_mac
        config.create_pcap()
        self.dut.send_expect("start", "testpmd>", 10)
        self.pmdout.wait_link_status_up(self.dut_port)
        config.send_pcap(self.tester_iface)
        # check whether detect vxlan type
        out = self.dut.get_session_output(timeout=2)
        print(out)
        self.verify(config.packet_type() in out, "Vxlan Packet not detected")

    def send_and_check(self, **kwargs):
        """
        send vxlan packet and check whether receive packet with correct
        checksum
        """
        # create pcap file with supplied arguments
        outer_ipv6 = False
        args = {}
        for arg in kwargs:
            if "invalid" not in arg:
                args[arg] = kwargs[arg]
                if "outer_ip6" in arg:
                    outer_ipv6 = True

        # if packet outer L3 is ipv6, should not enable hardware checksum
        if outer_ipv6:
            self.csum_set_sw("outer-ip", self.dut_port)
            self.csum_set_sw("outer-ip", self.recv_port)

        config = VxlanTestConfig(self, **args)
        # now cloud filter will default enable L2 mac filter, so dst mac must
        # be same
        config.outer_mac_dst = self.dut_port_mac
        # csum function will not auto add outer ip src address already, so update send packet src ip address
        if config.outer_ip6_src != "N/A":
            config.outer_ip6_src = config.outer_ip6_src
        else:
            config.outer_ip_src = config.outer_ip_src

        # csum function will not auto add outer ip src address already, so update send packet src ip address
        if config.outer_udp_dst == VXLAN_PORT:
            if config.inner_ip6_src != "N/A":
                config.inner_ip6_src = config.inner_ip6_src
            else:
                config.inner_ip_src = config.inner_ip_src

        # extract the checksum value of vxlan packet
        config.create_pcap()
        chksums_ref = config.get_chksums()
        self.logger.info("chksums_ref" + str(chksums_ref))

        # log the vxlan format
        arg_str = ""
        for arg in kwargs:
            arg_str += "[%s = %s]" % (arg, kwargs[arg])

        self.logger.info("vxlan packet %s" % arg_str)

        out = self.dut.send_expect("start", "testpmd>", 10)

        # create pcap file with supplied arguments
        config = VxlanTestConfig(self, **kwargs)
        config.outer_mac_dst = self.dut_port_mac
        config.create_pcap()

        # save the capture packet into pcap format
        inst = self.tester.tcpdump_sniff_packets(self.recv_iface)
        config.send_pcap(self.tester_iface)
        pkt = self.tester.load_tcpdump_sniff_packets(inst, timeout=3)

        # extract the checksum offload from saved pcap file
        chksums = config.get_chksums(pkt=pkt)
        self.logger.info("chksums" + str(chksums))

        out = self.dut.send_expect("stop", "testpmd>", 10)
        print(out)

        # verify detected l4 invalid checksum
        if "inner_l4_invalid" in kwargs:
            self.verify(
                self.pmdout.get_pmd_value("Bad-l4csum:", out) == 1,
                "Failed to count inner l4 chksum error",
            )

        # verify detected l3 invalid checksum
        if "ip_invalid" in kwargs:
            self.verify(
                self.pmdout.get_pmd_value("Bad-ipcsum:", out) == self.iperr_num + 1,
                "Failed to count inner ip chksum error",
            )
            self.iperr_num += 1

        # verify saved pcap checksum same to expected checksum
        for key in chksums_ref:
            self.verify(
                chksums[key] == chksums_ref[key],
                "%s not matched to %s" % (key, chksums_ref[key]),
            )

    def filter_and_check(self, rule, config, queue_id):
        """
        send vxlan packet and check whether receive packet in assigned queue
        """
        # create rule
        self.tunnel_filter_add(rule)

        # send vxlan packet
        config.create_pcap()
        self.dut.send_expect("start", "testpmd>", 10)
        self.pmdout.wait_link_status_up(self.dut_port)
        config.send_pcap(self.tester_iface)
        out = self.dut.get_session_output(timeout=2)
        print(out)

        queue = -1
        pattern = re.compile("- Receive queue=0x(\d)")
        m = pattern.search(out)
        if m is not None:
            queue = m.group(1)

        # verify received in expected queue
        self.verify(queue_id == int(queue), "invalid receive queue")

        # del rule
        args = [self.dut_port]
        self.tunnel_filter_del(*args)
        self.dut.send_expect("stop", "testpmd>", 10)

    def test_vxlan_ipv4_detect(self):
        """
        verify vxlan packet detection
        """
        if self.nic in ["ICE_25G-E810C_SFP", "ICE_100G-E810C_QSFP"]:
            print("Intel® Ethernet 700 Series support default none VECTOR")
            src_vec_model = "n"
        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/5C/1T", socket=self.ports_socket
        )

        self.dut.send_expect(
            r"./%s %s -- -i --disable-rss --rxq=4 --txq=4 --nb-cores=4 --portmask=%s"
            % (self.path, self.eal_para, self.portMask),
            "testpmd>",
            30,
        )

        self.dut.send_expect("set fwd rxonly", "testpmd>", 10)
        self.dut.send_expect("set verbose 1", "testpmd>", 10)
        self.enable_vxlan(self.dut_port)
        self.enable_vxlan(self.recv_port)
        self.pmdout.wait_link_status_up(self.dut_port)
        # check normal packet
        self.send_and_detect(outer_udp_dst=1234)
        # check vxlan + UDP inner packet
        self.send_and_detect(inner_l4_type="UDP")
        # check vxlan + TCP inner packet
        self.send_and_detect(inner_l4_type="TCP")
        # check vxlan + SCTP inner packet
        self.send_and_detect(inner_l4_type="SCTP")
        # check vxlan + vlan inner packet
        self.send_and_detect(outer_vlan=1)
        # check vlan vxlan + vlan inner packet
        self.send_and_detect(outer_vlan=1, inner_vlan=1)

        out = self.dut.send_expect("stop", "testpmd>", 10)
        self.dut.send_expect("quit", "#", 10)

    def test_vxlan_ipv6_detect(self):
        """
        verify vxlan packet detection with ipv6 header
        """
        if self.nic in ["ICE_25G-E810C_SFP", "ICE_100G-E810C_QSFP"]:
            print("Intel® Ethernet 700 Series support default none VECTOR")
            src_vec_model = "n"

        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/5C/1T", socket=self.ports_socket
        )

        self.dut.send_expect(
            r"./%s %s -- -i --disable-rss --rxq=4 --txq=4 --nb-cores=4 --portmask=%s"
            % (self.path, self.eal_para, self.portMask),
            "testpmd>",
            30,
        )

        self.dut.send_expect("set fwd rxonly", "testpmd>", 10)
        self.dut.send_expect("set verbose 1", "testpmd>", 10)
        self.enable_vxlan(self.dut_port)
        self.enable_vxlan(self.recv_port)
        self.pmdout.wait_link_status_up(self.dut_port)
        # check normal ipv6 packet
        self.send_and_detect(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            outer_udp_dst=1234,
        )
        # check ipv6 vxlan + UDP inner packet
        self.send_and_detect(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_type="UDP",
        )
        # check ipv6 vxlan + TCP inner packet
        self.send_and_detect(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_type="TCP",
        )
        # check ipv6 vxlan + SCTP inner packet
        self.send_and_detect(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_type="SCTP",
        )

        out = self.dut.send_expect("stop", "testpmd>", 10)
        self.dut.send_expect("quit", "#", 10)

    def test_vxlan_ipv4_checksum_offload(self):
        """
        verify vxlan packet checksum offload
        """
        # start testpmd with 2queue/1port

        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/5C/1T", socket=self.ports_socket
        )

        self.dut.send_expect(
            r"./%s %s -- -i --portmask=%s --enable-rx-cksum"
            % (self.path, self.eal_para, self.portMask),
            "testpmd>",
            30,
        )
        self.iperr_num = 0

        # disable vlan filter
        self.dut.send_expect("vlan set filter off %d" % self.dut_port, "testpmd")
        # enable tx checksum offload
        self.dut.send_expect("set fwd csum", "testpmd>", 10)
        self.dut.send_expect("port stop all", "testpmd>")
        self.csum_set_type("ip", self.recv_port)
        self.csum_set_type("outer-ip", self.recv_port)
        self.csum_set_type("udp", self.recv_port)
        self.csum_set_type("tcp", self.recv_port)
        self.csum_set_type("sctp", self.recv_port)
        self.dut.send_expect("port start all", "testpmd>")
        self.dut.send_expect("csum parse-tunnel on %d" % self.recv_port, "testpmd>", 10)

        self.enable_vxlan(self.dut_port)
        self.enable_vxlan(self.recv_port)
        self.pmdout.wait_link_status_up(self.dut_port)
        # check normal packet + ip checksum invalid
        self.send_and_check(outer_ip_invalid=1, outer_udp_dst=1234)
        # check vxlan packet + inner ip checksum invalid
        self.send_and_check(inner_ip_invalid=1)
        # check vxlan packet + outer ip checksum invalid
        self.send_and_check(outer_ip_invalid=1)
        # check vxlan packet + outer ip + inner ip checksum invalid
        self.send_and_check(outer_ip_invalid=1, inner_ip_invalid=1)
        # check vxlan packet + inner udp checksum invalid
        self.send_and_check(inner_l4_invalid=1)
        # check vxlan packet + inner tcp checksum invalid
        self.send_and_check(inner_l4_invalid=1, inner_l4_type="TCP")
        # check vxlan packet + inner sctp checksum invalid
        self.send_and_check(inner_l4_invalid=1, inner_l4_type="SCTP")
        # check vlan vxlan packet + outer ip checksum invalid
        self.send_and_check(outer_vlan=1, outer_ip_invalid=1)
        # check vlan vxlan packet + inner ip checksum invalid
        self.send_and_check(outer_vlan=1, inner_ip_invalid=1)
        # check vlan vxlan packet + outer&inner ip checksum invalid
        self.send_and_check(outer_vlan=1, outer_ip_invalid=1, inner_ip_invalid=1)
        # check vlan vxlan packet + inner vlan + outer ip checksum invalid
        self.send_and_check(outer_vlan=1, inner_vlan=1, outer_ip_invalid=1)
        # check vlan vxlan packet + inner vlan + inner ip checksum invalid
        self.send_and_check(outer_vlan=1, inner_vlan=1, inner_ip_invalid=1)
        # check vlan vxlan packet + inner vlan + outer&inner ip checksum
        # invalid
        self.send_and_check(
            outer_vlan=1, inner_vlan=1, outer_ip_invalid=1, inner_ip_invalid=1
        )
        # check vlan vxlan packet + inner vlan + inner udp checksum invalid
        self.send_and_check(outer_vlan=1, inner_l4_invalid=1, inner_l4_type="UDP")
        # check vlan vxlan packet + inner vlan + inner tcp checksum invalid
        self.send_and_check(outer_vlan=1, inner_l4_invalid=1, inner_l4_type="TCP")
        # check vlan vxlan packet + inner vlan + inner sctp checksum invalid
        self.send_and_check(outer_vlan=1, inner_l4_invalid=1, inner_l4_type="SCTP")

        self.dut.send_expect("quit", "#", 10)

    def test_vxlan_ipv6_checksum_offload(self):
        """
        verify vxlan packet checksum offload with ipv6 header
        not support ipv6 + sctp
        """
        # start testpmd with 2queue/1port

        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/5C/1T", socket=self.ports_socket
        )

        self.dut.send_expect(
            r"./%s %s -- -i --portmask=%s --enable-rx-cksum"
            % (self.path, self.eal_para, self.portMask),
            "testpmd>",
            30,
        )
        self.iperr_num = 0

        # disable vlan filter
        self.dut.send_expect("vlan set filter off %d" % self.dut_port, "testpmd")
        # enable tx checksum offload
        self.dut.send_expect("set fwd csum", "testpmd>", 10)
        self.csum_set_type("outer-ip", self.recv_port)
        self.csum_set_type("udp", self.recv_port)
        self.csum_set_type("outer-udp", self.recv_port)
        self.csum_set_type("tcp", self.recv_port)
        self.csum_set_type("sctp", self.recv_port)
        self.dut.send_expect("csum parse-tunnel on %d" % self.recv_port, "testpmd>", 10)

        self.enable_vxlan(self.dut_port)
        self.enable_vxlan(self.recv_port)
        self.pmdout.wait_link_status_up(self.dut_port)
        # check normal ipv6 packet
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0", outer_ip6_dst="FE80:0:0:0:0:0:0:1"
        )
        # check normal ipv6 packet + ip checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            outer_udp_dst=1234,
        )
        # check ipv6 vxlan packet + inner ip checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_ip_invalid=1,
        )
        # check ipv6 vxlan packet + inner udp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="UDP",
        )
        # check ipv6 vxlan packet + inner udp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="UDP",
        )
        # check ipv6 vxlan packet + inner tcp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="TCP",
        )
        # check ipv6 vlan vxlan packet + inner udp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="UDP",
            outer_vlan=1,
        )
        # check ipv6 vlan vxlan packet + inner tcp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="TCP",
            outer_vlan=1,
        )
        # check ipv6 vlan vxlan packet + vlan + inner udp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="UDP",
            outer_vlan=1,
            inner_vlan=1,
        )
        # check ipv6 vlan vxlan packet + vlan + inner tcp checksum invalid
        self.send_and_check(
            outer_ip6_src="FE80:0:0:0:0:0:0:0",
            outer_ip6_dst="FE80:0:0:0:0:0:0:1",
            inner_l4_invalid=1,
            inner_l4_type="TCP",
            outer_vlan=1,
            inner_vlan=1,
        )

        self.dut.send_expect("quit", "#", 10)

    def test_tunnel_filter(self):
        """
        verify tunnel filter feature
        """
        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/5C/1T", socket=self.ports_socket
        )

        self.dut.send_expect(
            r"./%s %s -- -i --disable-rss --rxq=%d --txq=%d --nb-cores=4 --portmask=%s"
            % (self.path, self.eal_para, MAX_TXQ_RXQ, MAX_TXQ_RXQ, self.portMask),
            "testpmd>",
            30,
        )

        self.dut.send_expect("set fwd rxonly", "testpmd>", 10)
        self.dut.send_expect("set verbose 1", "testpmd>", 10)
        self.enable_vxlan(self.dut_port)
        self.enable_vxlan(self.recv_port)
        self.pmdout.wait_link_status_up(self.dut_port)
        config = VxlanTestConfig(self)
        config_vlan = VxlanTestConfig(self, inner_vlan=1)
        config.outer_mac_dst = self.dut_port_mac
        config_vlan.outer_mac_dst = self.dut_port_mac
        expect_queue = randint(1, MAX_TXQ_RXQ - 1)

        rule_list = [
            # check inner mac + inner vlan filter can work
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan / eth dst is {} / vlan tci is {} / end actions pf "
            "/ queue index {} / end".format(
                self.dut_port,
                config_vlan.inner_mac_dst,
                config_vlan.inner_vlan,
                expect_queue,
            ),
            # check inner mac + inner vlan + tunnel id filter can work
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan vni is {} / eth dst is {} "
            "/ vlan tci is {} / end actions pf / queue index {} / end".format(
                self.dut_port,
                config_vlan.vni,
                config_vlan.inner_mac_dst,
                config_vlan.inner_vlan,
                expect_queue,
            ),
            # check inner mac + tunnel id filter can work
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan vni is {} / eth dst is {} / end actions pf "
            "/ queue index {} / end".format(
                self.dut_port, config.vni, config.inner_mac_dst, expect_queue
            ),
            # check inner mac filter can work
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan / eth dst is {} / end actions pf / queue index {} "
            "/ end".format(self.dut_port, config.inner_mac_dst, expect_queue),
            # check outer mac + inner mac + tunnel id filter can work
            "flow create {} ingress pattern eth dst is {} / ipv4 / udp / vxlan vni is {} / eth dst is {} "
            "/ end actions pf / queue index {} / end".format(
                self.dut_port,
                config.outer_mac_dst,
                config.vni,
                config.inner_mac_dst,
                expect_queue,
            )
            # iip not supported by now
            # 'flow create {} ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 dst is {} / end actions pf '
            # '/ queue index {} / end'.format(self.dut_port,
            #                                 config.inner_ip_dst,
            #                                 queue)
        ]

        for rule in rule_list:
            if "vlan tci is" in rule:
                self.filter_and_check(rule, config_vlan, expect_queue)
            else:
                self.filter_and_check(rule, config, expect_queue)

        self.dut.send_expect("quit", "#", 10)

    def test_tunnel_filter_invalid(self):
        """
        verify tunnel filter parameter check function
        """
        # invalid parameter
        queue_id = 3

        config = VxlanTestConfig(self)
        config.outer_mac_dst = self.dut_port_mac

        self.eal_para = self.dut.create_eal_parameters(
            cores="1S/5C/1T", socket=self.ports_socket
        )

        self.dut.send_expect(
            r"./%s %s -- -i --disable-rss --rxq=4 --txq=4 --nb-cores=4 --portmask=%s"
            % (self.path, self.eal_para, self.portMask),
            "testpmd>",
            30,
        )

        self.enable_vxlan(self.dut_port)
        self.enable_vxlan(self.recv_port)
        self.pmdout.wait_link_status_up(self.dut_port)
        rule = (
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan vni is {} / eth dst is {} / end actions pf "
            "/ queue index {} / end".format(
                self.dut_port, config.vni, self.invalid_mac, queue_id
            )
        )
        out = self.tunnel_filter_add_nocheck(rule)
        self.verify("Bad arguments" in out, "Failed to detect invalid mac")

        rule = (
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan vni is {} / eth / ipv4 dst is {} "
            "/ end actions pf / queue index {} / end".format(
                self.dut_port, config.vni, self.invalid_ip, queue_id
            )
        )
        out = self.tunnel_filter_add_nocheck(rule)
        self.verify("Bad arguments" in out, "Failed to detect invalid ip")

        # testpmd is not support
        # rule = 'flow create {} ingress pattern eth / ipv4 / udp / vxlan vni is {} / eth dst is {} / vlan vid is {} ' \
        #        '/ end actions pf / queue index {} / end'.format(self.dut_port,
        #                                                         config.vni,
        #                                                         config.inner_mac_dst,
        #                                                         self.invalid_vlan,
        #                                                         queue_id)
        # out = self.tunnel_filter_add_nocheck(rule)
        # self.verify("Invalid argument" in out, "Failed to detect invalid vlan")

        rule = (
            "flow create {} ingress pattern eth / ipv4 / udp / vxlan vni is {} / eth dst is {} / end actions pf "
            "/ queue index {} / end".format(
                self.dut_port, config.vni, config.inner_mac_dst, self.invalid_queue
            )
        )
        out = self.tunnel_filter_add_nocheck(rule)
        self.verify("Invalid queue ID" in out, "Failed to detect invalid queue")

        self.dut.send_expect("stop", "testpmd>", 10)
        self.dut.send_expect("quit", "#", 10)

    def config_tunnelfilter(self, dut_port, recv_port, perf_config, pcapfile):
        pkts = []
        config = VxlanTestConfig(self, payload_size=self.vxlan_payload - 4)
        config.inner_vlan = self.default_vlan
        config.outer_mac_dst = self.dut.get_mac_address(dut_port)
        config.pcap_file = pcapfile

        tun_filter = perf_config["tunnel_filter"]
        recv_queue = perf_config["recvqueue"]
        # there's known bug that if enable vxlan, rss will be disabled
        if tun_filter == "None" and recv_queue == "Multi":
            print((utils.RED("RSS and Tunel filter can't enable in the same time")))
        else:
            self.enable_vxlan(dut_port)

        if tun_filter != "None":
            rule_config = {
                "dut_port": dut_port,
                "outer_mac_dst": config.outer_mac_dst,
                "inner_mac_dst": config.inner_mac_dst,
                "inner_ip_dst": config.inner_ip_dst,
                "inner_vlan": config.inner_vlan,
                "tun_filter": tun_filter,
                "vni": config.vni,
                "queue": 0,
            }
            self.perf_tunnel_filter_set_rule(rule_config)

        if perf_config["Packet"] == "Normal":
            config.outer_udp_dst = 63
            config.outer_mac_dst = self.dut.get_mac_address(dut_port)
            config.payload_size = (
                PACKET_LEN - HEADER_SIZE["eth"] - HEADER_SIZE["ip"] - HEADER_SIZE["udp"]
            )

        # add default pkt into pkt list
        pkt = config.create_pcap()
        pkts.append(pkt)

        # add other pkts into pkt list when enable multi receive queues
        if recv_queue == "Multi" and tun_filter != "None":
            for queue in range(self.tunnel_multiqueue - 1):
                if "imac" in tun_filter:
                    config.inner_mac_dst = "00:00:20:00:00:0%d" % (queue + 2)
                if "ivlan" in tun_filter:
                    config.inner_vlan = queue + 2
                if "tenid" in tun_filter:
                    config.vni = queue + 2

                # add tunnel filter the same as pkt
                pkt = config.create_pcap()
                pkts.append(pkt)

                rule_config = {
                    "dut_port": dut_port,
                    "outer_mac_dst": config.outer_mac_dst,
                    "inner_mac_dst": config.inner_mac_dst,
                    "inner_ip_dst": config.inner_ip_dst,
                    "inner_vlan": config.inner_vlan,
                    "tun_filter": tun_filter,
                    "vni": config.vni,
                    "queue": (queue + 1),
                }
                self.perf_tunnel_filter_set_rule(rule_config)

        # save pkt list into pcap file
        wrpcap(config.pcap_file, pkts)
        self.tester.session.copy_file_to(config.pcap_file)

    def combine_pcap(self, dest_pcap, src_pcap):
        pkts = rdpcap(dest_pcap)
        if len(pkts) != 1:
            return

        pkts_src = rdpcap(src_pcap)
        pkts += pkts_src

        wrpcap(dest_pcap, pkts)

    def test_perf_vxlan_tunnelfilter_performance_2ports(self):
        self.result_table_create(self.tunnel_header)
        core_list = self.dut.get_core_list(
            "1S/%dC/1T" % (self.tunnel_multiqueue * 2 + 1), socket=self.ports_socket
        )

        pmd_temp = (
            "./%s %s -- -i --disable-rss --rxq=2 --txq=2 --nb-cores=4 --portmask=%s"
        )

        for perf_config in self.tunnel_perf:
            tun_filter = perf_config["tunnel_filter"]
            recv_queue = perf_config["recvqueue"]
            print(
                (
                    utils.GREEN(
                        "Measure tunnel performance of [%s %s %s]"
                        % (perf_config["Packet"], tun_filter, recv_queue)
                    )
                )
            )

            if tun_filter == "None" and recv_queue == "Multi":
                pmd_temp = (
                    "./%s %s -- -i --rss-udp --rxq=2 --txq=2 --nb-cores=4 --portmask=%s"
                )

            self.eal_para = self.dut.create_eal_parameters(cores=core_list)
            pmd_cmd = pmd_temp % (self.path, self.eal_para, self.portMask)
            self.dut.send_expect(pmd_cmd, "testpmd> ", 100)

            # config flow
            self.config_tunnelfilter(
                self.dut_port, self.recv_port, perf_config, "flow1.pcap"
            )
            # config the flows
            tgen_input = []
            tgen_input.append(
                (
                    self.tester.get_local_port(self.dut_port),
                    self.tester.get_local_port(self.recv_port),
                    "flow1.pcap",
                )
            )

            if BIDIRECT:
                self.config_tunnelfilter(
                    self.recv_port, self.dut_port, perf_config, "flow2.pcap"
                )
                tgen_input.append(
                    (
                        self.tester.get_local_port(self.recv_port),
                        self.tester.get_local_port(self.dut_port),
                        "flow2.pcap",
                    )
                )

            self.dut.send_expect("set fwd io", "testpmd>", 10)
            self.dut.send_expect("start", "testpmd>", 10)
            self.pmdout.wait_link_status_up(self.dut_port)
            if BIDIRECT:
                wirespeed = self.wirespeed(self.nic, PACKET_LEN, 2)
            else:
                wirespeed = self.wirespeed(self.nic, PACKET_LEN, 1)

            # run traffic generator
            use_vm = True if recv_queue == "Multi" and tun_filter == "None" else False
            _, pps = self.suite_measure_throughput(tgen_input, use_vm=use_vm)

            pps /= 1000000.0
            perf_config["Mpps"] = pps
            perf_config["pct"] = pps * 100 / wirespeed

            out = self.dut.send_expect("stop", "testpmd>", 10)
            self.dut.send_expect("quit", "# ", 10)

            # verify every queue work fine
            check_queue = 0
            if recv_queue == "Multi":
                for queue in range(check_queue):
                    self.verify(
                        "Queue= %d -> TX Port" % (queue) in out,
                        "Queue %d no traffic" % queue,
                    )

            table_row = [
                perf_config["Packet"],
                tun_filter,
                recv_queue,
                perf_config["Mpps"],
                perf_config["pct"],
            ]

            self.result_table_add(table_row)

        self.result_table_print()

    def test_perf_vxlan_checksum_performance_2ports(self):
        self.result_table_create(self.chksum_header)
        vxlan = VxlanTestConfig(self, payload_size=self.vxlan_payload)
        vxlan.outer_mac_dst = self.dut.get_mac_address(self.dut_port)
        vxlan.pcap_file = "vxlan1.pcap"
        vxlan.inner_mac_dst = "00:00:20:00:00:01"
        vxlan.create_pcap()

        vxlan_queue = VxlanTestConfig(self, payload_size=self.vxlan_payload)
        vxlan_queue.outer_mac_dst = self.dut.get_mac_address(self.dut_port)
        vxlan_queue.pcap_file = "vxlan1_1.pcap"
        vxlan_queue.inner_mac_dst = "00:00:20:00:00:02"
        vxlan_queue.create_pcap()

        # socket/core/thread
        core_list = self.dut.get_core_list(
            "1S/%dC/1T" % (self.tunnel_multiqueue * 2 + 1), socket=self.ports_socket
        )
        core_mask = utils.create_mask(core_list)

        self.dut_ports = self.dut.get_ports_performance(force_different_nic=False)
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])

        for cal in self.cal_type:
            recv_queue = cal["recvqueue"]
            print(
                (
                    utils.GREEN(
                        "Measure checksum performance of [%s %s %s]"
                        % (cal["Type"], recv_queue, cal["csum"])
                    )
                )
            )

            # configure flows
            tgen_input = []
            if recv_queue == "Multi":
                tgen_input.append((tx_port, rx_port, "vxlan1.pcap"))
                tgen_input.append((tx_port, rx_port, "vxlan1_1.pcap"))
            else:
                tgen_input.append((tx_port, rx_port, "vxlan1.pcap"))

            # multi queue and signle queue commands
            if recv_queue == "Multi":
                pmd_temp = "./%s %s -- -i --disable-rss --rxq=2 --txq=2 --nb-cores=4 --portmask=%s"
            else:
                pmd_temp = "./%s %s -- -i --nb-cores=2 --portmask=%s"

            self.eal_para = self.dut.create_eal_parameters(cores=core_list)
            pmd_cmd = pmd_temp % (self.path, self.eal_para, self.portMask)

            self.dut.send_expect(pmd_cmd, "testpmd> ", 100)
            self.dut.send_expect("set fwd csum", "testpmd>", 10)
            self.enable_vxlan(self.dut_port)
            self.enable_vxlan(self.recv_port)
            self.pmdout.wait_link_status_up(self.dut_port)

            # redirect flow to another queue by tunnel filter
            rule_config = {
                "dut_port": self.dut_port,
                "outer_mac_dst": vxlan.outer_mac_dst,
                "inner_mac_dst": vxlan.inner_mac_dst,
                "inner_ip_dst": vxlan.inner_ip_dst,
                "inner_vlan": 0,
                "tun_filter": "imac",
                "vni": vxlan.vni,
                "queue": 0,
            }
            self.perf_tunnel_filter_set_rule(rule_config)

            if recv_queue == "Multi":
                rule_config = {
                    "dut_port": self.dut_port,
                    "outer_mac_dst": vxlan_queue.outer_mac_dst,
                    "inner_mac_dst": vxlan_queue.inner_mac_dst,
                    "inner_ip_dst": vxlan_queue.inner_ip_dst,
                    "inner_vlan": 0,
                    "tun_filter": "imac",
                    "vni": vxlan.vni,
                    "queue": 1,
                }
                self.perf_tunnel_filter_set_rule(rule_config)

            for pro in cal["csum"]:
                self.csum_set_type(pro, self.dut_port)
                self.csum_set_type(pro, self.recv_port)

            self.dut.send_expect("start", "testpmd>", 10)

            wirespeed = self.wirespeed(self.nic, PACKET_LEN, 1)

            # run traffic generator
            _, pps = self.suite_measure_throughput(tgen_input)

            pps /= 1000000.0
            cal["Mpps"] = pps
            cal["pct"] = pps * 100 / wirespeed

            out = self.dut.send_expect("stop", "testpmd>", 10)
            self.dut.send_expect("quit", "# ", 10)

            # verify every queue work fine
            check_queue = 1
            if recv_queue == "Multi":
                for queue in range(check_queue):
                    self.verify(
                        "Queue= %d -> TX Port" % (queue) in out,
                        "Queue %d no traffic" % queue,
                    )

            table_row = [cal["Type"], recv_queue, cal["Mpps"], cal["pct"]]
            self.result_table_add(table_row)

        self.result_table_print()

    def enable_vxlan(self, port):
        self.dut.send_expect(
            "rx_vxlan_port add %d %d" % (VXLAN_PORT, port), "testpmd>", 10
        )

    def csum_set_type(self, proto, port):
        self.dut.send_expect("port stop all", "testpmd>")
        out = self.dut.send_expect("csum set %s hw %d" % (proto, port), "testpmd>", 10)
        self.dut.send_expect("port start all", "testpmd>")
        self.verify("Bad arguments" not in out, "Failed to set vxlan csum")
        self.verify("error" not in out, "Failed to set vxlan csum")

    def csum_set_sw(self, proto, port):
        self.dut.send_expect("port stop all", "testpmd>")
        out = self.dut.send_expect("csum set %s sw %d" % (proto, port), "testpmd>", 10)
        self.dut.send_expect("port start all", "testpmd>")
        self.verify("Bad arguments" not in out, "Failed to set vxlan csum")
        self.verify("error" not in out, "Failed to set vxlan csum")

    def tunnel_filter_add(self, rule):
        out = self.dut.send_expect(rule, "testpmd>", 3)
        self.verify("Flow rule #0 created" in out, "Flow rule create failed")
        return out

    def tunnel_filter_add_nocheck(self, rule):
        out = self.dut.send_expect(rule, "testpmd>", 3)
        return out

    def tunnel_filter_del(self, *args):
        out = self.dut.send_expect("flow flush 0", "testpmd>", 10)
        return out

    def set_up(self):
        """
        Run before each test case.
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
