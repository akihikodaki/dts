# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#

"""
DPDK Test suite.

Test the support of RSS Key Update by Poll Mode Drivers.

"""

import random
import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

queue = 16
reta_entries = []
reta_num = 128
iptypes = {
    "ipv4-sctp": "sctp",
    "ipv4-other": "ip",
    "ipv4-frag": "ip",
    "ipv4-udp": "udp",
    "ipv4-tcp": "tcp",
    "ipv6-other": "ip",
    "ipv6-sctp": "sctp",
    "ipv6-udp": "udp",
    "ipv6-tcp": "tcp",
    "ipv6-frag": "ip",
}


class TestRssKeyUpdate(TestCase):
    def send_packet(self, itf, tran_type, symmetric):
        """
        Sends packets.
        """
        packet_list = {
            "ipv4-sctp": 'IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1024,dport=1024,tag=1)',
            "ipv4-other": 'IP(src="192.168.0.%d", dst="192.168.0.%d")',
            "ipv4-frag": 'IP(src="192.168.0.%d", dst="192.168.0.%d",frag=1,flags="MF")',
            "ipv4-udp": 'IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1024)',
            "ipv4-tcp": 'IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1024)',
            "ipv6-other": 'IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")',
            "ipv6-sctp": 'IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(sport=1024,dport=1024,tag=1)',
            "ipv6-udp": 'IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(sport=1024,dport=1024)',
            "ipv6-tcp": 'IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/TCP(sport=1024,dport=1024)',
            "ipv6-frag": 'IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d",nh=44)/IPv6ExtHdrFragment()',
        }

        received_pkts = []
        self.tester.scapy_foreground()
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)

        # send packet with different source and dest ip
        if tran_type in packet_list.keys():
            packet_temp = (
                r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/%s], iface="%s")'
                % (mac, itf, packet_list[tran_type], itf)
            )
            for i in range(10):
                packet = packet_temp % (i + 1, i + 2)
                self.tester.scapy_append(packet)
                if symmetric:
                    packet2 = packet_temp % (i + 2, i + 1)
                    self.tester.scapy_append(packet2)
            self.tester.scapy_execute()
            time.sleep(0.5)
        else:
            print("\ntran_type error!\n")

        out = self.dut.get_session_output(timeout=1)
        self.dut.send_expect("stop", "testpmd>")
        lines = out.split("\r\n")
        reta_line = {}
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.startswith("port "):
                reta_line = {}
                rexp = r"port (\d+)/queue (\d+): received (\d+) packets"
                m = re.match(rexp, line)
                if m:
                    reta_line["port"] = m.group(1)
                    reta_line["queue"] = m.group(2)

            elif len(line) != 0 and line.startswith("src="):
                if "RSS hash" not in line:
                    continue
                for item in line.split("-"):
                    item = item.strip()
                    if item.startswith("RSS hash"):
                        name, value = item.split("=", 1)

                reta_line[name.strip()] = value.strip()
                received_pkts.append(reta_line)

        return self.verifyResult(received_pkts, symmetric)

    def verifyResult(self, reta_lines, symmetric):
        """
        Verify whether or not the result passes.
        """
        global pre_RSS_hash
        result = []
        key_id = {}
        self.verify(len(reta_lines) > 0, "No packet received!")
        self.result_table_create(
            [
                "packet index",
                "hash value",
                "hash index",
                "queue id",
                "actual queue id",
                "pass ",
            ]
        )

        for i, tmp_reta_line in enumerate(reta_lines):
            # compute the hash result of five tuple into the 7 LSBs value.
            hash_index = int(tmp_reta_line["RSS hash"], 16) % reta_num
            if reta_entries[hash_index] == int(tmp_reta_line["queue"]):
                status = "true"
                result.insert(i, 0)
                if symmetric:
                    if i % 2 == 1:
                        if pre_RSS_hash == tmp_reta_line["RSS hash"]:
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
                [
                    i,
                    tmp_reta_line["RSS hash"],
                    hash_index,
                    reta_entries[hash_index],
                    tmp_reta_line["queue"],
                    status,
                ]
            )
            key_id[tmp_reta_line["RSS hash"]] = reta_entries[hash_index]

        self.result_table_print()
        self.verify(sum(result) == 0, "the reta update function failed!")
        return key_id

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.verify(
            self.nic
            in [
                "ICE_25G-E810C_SFP",
                "ICE_100G-E810C_QSFP",
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_X722",
                "I40E_25G-25G_SFP28",
                "IXGBE_10G-82599_SFP",
                "I40E_10G-10G_BASE_T_BC",
                "IGC-I225_LM",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        global reta_num
        global iptypes
        global queue
        if self.nic in ["IGC-I225_LM"]:
            queue = 4

        if self.nic in [
            "I40E_10G-SFP_XL710",
            "I40E_40G-QSFP_A",
            "I40E_40G-QSFP_B",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_X722",
            "I40E_25G-25G_SFP28",
            "I40E_10G-10G_BASE_T_BC",
        ]:
            reta_num = 512
        elif self.nic in ["IXGBE_10G-82599_SFP", "IGC-I225_LM"]:
            reta_num = 128
            iptypes = {
                "ipv4-other": "ip",
                "ipv4-frag": "ip",
                "ipv4-udp": "udp",
                "ipv4-tcp": "tcp",
                "ipv6-other": "ip",
                "ipv6-udp": "udp",
                "ipv6-tcp": "tcp",
                "ipv6-frag": "ip",
            }
        else:
            self.verify(False, f"NIC Unsupported: {self.nic}")

        cores = self.dut.get_core_list("all")
        self.coremask = utils.create_mask(cores)

        ports = self.dut.get_ports(self.nic)
        self.ports_socket = self.dut.get_numa_id(ports[0])
        self.verify(len(ports) >= 1, "Not enough ports available")

        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        Run before each test case.
        """
        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        self.itf = self.tester.get_interface(localPort)

        self.dut.kill_all()

        self.pmdout.start_testpmd("all", f"--rxq={queue} --txq={queue}")

    def test_set_hash_key_toeplitz(self):

        self.dut.send_expect("set verbose 8", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.dut.send_expect(f"set nbcore {queue + 1}", "testpmd> ")
        key = "4439796BB54C5023B675EA5B124F9F30B8A2C03DDFDC4D02A08C9B334AF64A4C05C6FA343958D8557D99583AE138C92E81150366"
        ck = "4439796BB54C50f3B675EF5B124F9F30B8A2C0FFFFDC4D02A08C9B334FF64A4C05C6FA343958D855FFF9583AE138C92E81150FFF"

        # configure the reta with specific mappings.
        for i in range(reta_num):
            reta_entries.insert(i, random.randint(0, queue - 1))
            self.dut.send_expect(
                f"port config 0 rss reta ({i},{reta_entries[i]})", "testpmd> "
            )

        for iptype, rsstype in list(iptypes.items()):
            self.logger.info(
                f"***********************{iptype} rss test********************************"
            )
            self.dut.send_expect(
                f"port config 0 rss-hash-key {iptype} {key}", "testpmd> "
            )
            self.dut.send_expect("flow flush 0", "testpmd> ")
            cmd = f"flow create 0 ingress pattern eth / ipv4 / end actions rss types {iptype} end queues end func toeplitz / end"
            if "sctp" in iptype or "udp" in iptype or "tcp" in iptype:
                cmd = cmd.replace("/ ipv4 /", f"/ ipv4 / {rsstype} /")
            if "ipv6" in iptype:
                cmd = cmd.replace("ipv4", "ipv6")
            self.dut.send_expect(cmd, "testpmd> ")
            out = self.dut.send_expect(f"port config all rss {rsstype}", "testpmd> ")
            self.verify(
                "error" not in out, "Configuration of RSS hash failed: Invalid argument"
            )
            ori_output = self.send_packet(self.itf, iptype, False)
            self.dut.send_expect("show port 0 rss-hash key", "testpmd> ")
            self.dut.send_expect(
                f"port config 0 rss-hash-key {iptype} {ck}", "testpmd> "
            )
            self.dut.send_expect("flow flush 0", "testpmd> ")
            cmd = f"flow create 0 ingress pattern eth / ipv4 / end actions rss types {iptype} end queues end func toeplitz / end"
            if "sctp" in iptype or "udp" in iptype or "tcp" in iptype:
                cmd = cmd.replace("/ ipv4 /", f"/ ipv4 / {rsstype} /")
            if "ipv6" in iptype:
                cmd = cmd.replace("ipv4", "ipv6")
            self.dut.send_expect(cmd, "testpmd> ")
            new_output = self.send_packet(self.itf, iptype, False)
            self.verify(
                ori_output != new_output,
                "before and after results are the same, hash key configuration failed!",
            )

    def test_set_hash_key_toeplitz_symmetric(self):

        self.dut.send_expect("set verbose 8", "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.dut.send_expect(f"set nbcore {queue + 1}", "testpmd> ")
        key = "4439796BB54C5023B675EA5B124F9F30B8A2C03DDFDC4D02A08C9B334AF64A4C05C6FA343958D8557D99583AE138C92E81150366"
        ck = "4439796BB54C50f3B675EF5B124F9F30B8A2C0FFFFDC4D02A08C9B334FF64A4C05C6FA343958D855FFF9583AE138C92E81150FFF"
        rule_action = "func symmetric_toeplitz queues end / end"

        # configure the reta with specific mappings.
        for i in range(reta_num):
            reta_entries.insert(i, random.randint(0, queue - 1))
            self.dut.send_expect(
                f"port config 0 rss reta ({i},{reta_entries[i]})", "testpmd> "
            )

        for iptype, rsstype in list(iptypes.items()):
            self.logger.info(
                f"***********************{iptype} rss test********************************"
            )
            self.dut.send_expect(
                f"port config 0 rss-hash-key {iptype} {key}", "testpmd> "
            )
            self.dut.send_expect("flow flush 0", "testpmd> ")
            rule_cmd = f"flow create 0 ingress pattern eth / ipv4 / end actions rss types {iptype} end queues end {rule_action}"
            if "sctp" in iptype or "udp" in iptype or "tcp" in iptype:
                rule_cmd = rule_cmd.replace("/ ipv4 /", f"/ ipv4 / {rsstype} /")
            if "ipv6" in iptype:
                rule_cmd = rule_cmd.replace("ipv4", "ipv6")

            self.dut.send_expect(rule_cmd, "testpmd> ")
            out = self.dut.send_expect(f"port config all rss {rsstype}", "testpmd> ")
            self.verify(
                "error" not in out, "configuration of rss hash failed: invalid argument"
            )
            ori_output = self.send_packet(self.itf, iptype, True)
            out = self.dut.send_expect("show port 0 rss-hash key", "testpmd> ")
            self.verify("rss disable" not in out, "rss is disable!")
            self.dut.send_expect(
                f"port config 0 rss-hash-key {iptype} {ck}", "testpmd> "
            )

            self.dut.send_expect("flow flush 0", "testpmd> ")
            cmd = f"flow create 0 ingress pattern eth / ipv4 / end actions rss types {iptype} end queues end {rule_action}"
            if "sctp" in iptype or "udp" in iptype or "tcp" in iptype:
                cmd = cmd.replace("/ ipv4 /", f"/ ipv4 / {rsstype} /")
            if "ipv6" in iptype:
                cmd = cmd.replace("ipv4", "ipv6")

            self.dut.send_expect(cmd, "testpmd> ")
            new_output = self.send_packet(self.itf, iptype, True)
            self.verify(
                ori_output != new_output,
                "before and after results are the same, hash key configuration failed!",
            )

    def test_set_hash_key_short_long(self):

        nic_rss_key_size = {
            "ICE_25G-E810C_SFP": 52,
            "ICE_100G-E810C_QSFP": 52,
            "I40E_10G-SFP_XL710": 52,
            "I40E_40G-QSFP_A": 52,
            "I40E_40G-QSFP_B": 52,
            "I40E_25G-25G_SFP28": 52,
            "IXGBE_10G-82599_SFP": 40,
            "e1000": 40,
            "I40E_10G-SFP_X722": 52,
            "I40E_10G-10G_BASE_T_X722": 52,
            "hi1822": 40,
            "cavium_a063": 48,
            "cavium_a064": 48,
            "I40E_10G-10G_BASE_T_BC": 52,
            "IXGBE_10G-X550EM_X_10G_T": 40,
            "IXGBE_10G-X550T": 40,
            "IGC-I225_LM": 40,
            "IXGBE_10G-X540T": 40,
        }

        self.verify(
            self.nic in list(nic_rss_key_size.keys()),
            f"Not supported rss key on {self.nic}",
        )

        # Check supported hash key size
        out = self.dut.send_expect("show port info all", "testpmd> ", 120)
        self.verify(
            f"Hash key size in bytes: {nic_rss_key_size[self.nic]}" in out,
            "not expected hash key size!",
        )

        test_keys = {
            "4439796BB54C50f3B675EF5B124F9F30B8A2C0FFFFDC4D02A08C9B334FF64A4C05C6FA343958D855FFF9583AE138C92E81150FFFFF": "longer",
            "4439796BB54C50f3B675EF5B124F9F30B8A2C0DC4D02A08C9B334FF64A4C05C6FA343958D855FFF9583AE138C92E81150FFF": "shorter",
        }

        # config key length longer/shorter than 104 hexa-decimal numbers
        for key, error in test_keys.items():
            out = self.dut.send_expect(
                f"port config 0 rss-hash-key ipv4-udp {key}", "testpmd> "
            )
            self.verify(
                "invalid" in out,
                f"Try to set hash key {error} than 104 hexa-decimal numbers!",
            )

        # config ket length same as 104 hex-decimal numbers and keep the config
        key = "4439796BB54C50f3B675EF5B124F9F30B8A2C0FFFFDC4D02A08C9B334FF64A4C05C6FA343958D855FFF9583AE138C92E81150FFF"
        out = self.dut.send_expect(
            f"port config 0 rss-hash-key ipv4-udp {key}", "testpmd> "
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.pmdout.quit()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
