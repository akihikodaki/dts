# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test RSS reta (redirection table) update function.
"""
import random
import re
import textwrap
import time

import framework.utils as utils

testQueues = [2, 9, 16]
reta_entries = []
reta_lines = []

from framework.pmd_output import PmdOutput

# Use scapy to send packets with different source and dest ip.
# and collect the hash result of five tuple and the queue id.
from framework.test_case import TestCase


class TestPmdrssreta(TestCase):
    def send_packet(self, itf, tran_type):
        """
        Sends packets.
        """
        global reta_lines

        self.tester.scapy_foreground()
        self.tester.scapy_append('sys.path.append("./")')
        self.tester.scapy_append("from sctp import *")
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)
        # send packet with different source and dest ip
        if tran_type == "IPV4":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV4&TCP":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1024)], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV4&UDP":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1024)], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV6":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV6&TCP":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/TCP(sport=1024,dport=1024)], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV6&UDP":
            for i in range(16):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(sport=1024,dport=1024)], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        else:
            print("\ntran_type error!\n")
        out = self.dut.get_session_output(timeout=1)
        self.dut.send_expect("stop", "testpmd>")
        lines = out.split("\r\n")
        reta_line = {}

        # collect the hash result of five tuple and the queue id
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.startswith(("src=",)):
                for item in line.split("-"):
                    item = item.strip()
                    if item.startswith("RSS hash"):
                        name, value = item.split("=", 1)
                        print(name + "-" + value)

                reta_line[name.strip()] = value.strip()
                reta_lines.append(reta_line)
                reta_line = {}
            elif len(line) != 0 and line.strip().startswith("port "):
                rexp = r"port (\d)/queue (\d{1,2}): received (\d) packets"
                m = re.match(rexp, line.strip())
                if m:
                    reta_line["port"] = m.group(1)
                    reta_line["queue"] = m.group(2)
            elif len(line) != 0 and line.startswith("stop"):
                break
            else:
                pass

        self.verifyResult()

    def verifyResult(self):
        """
        Verify whether or not the result passes.
        """

        global reta_lines
        result = []
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

        i = 0
        for tmp_reta_line in reta_lines:
            status = "false"
            if self.nic in ["cavium_a063", "cavium_a064"]:
                # compute the hash index calculation
                hash_index = int(tmp_reta_line["RSS hash"], 16) % 64
            elif self.nic in ["hi1822"]:
                hash_index = int(tmp_reta_line["RSS hash"], 16) % 256
            elif self.nic in [
                "IXGBE_10G-82599_SFP",
                "IGC-I226_LM",
                "IGC-I225_LM",
                "IXGBE_10G-X540T",
            ]:
                # compute the hash result of five tuple into the 7 LSBs value.
                hash_index = int(tmp_reta_line["RSS hash"], 16) % 128
            else:
                # compute the hash result of five tuple into the 7 LSBs value.
                hash_index = int(tmp_reta_line["RSS hash"], 16) % 512
            if reta_entries[hash_index] == int(tmp_reta_line["queue"]):
                status = "true"
                result.insert(i, 0)
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
            i = i + 1

        self.result_table_print()
        reta_lines = []
        self.verify(sum(result) == 0, "the reta update function failed!")

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
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
        pass

    def test_pmdrss_reta(self):
        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(localPort)
        iptypes = {
            "IPV4": "ip",
            "IPV4&UDP": "udp",
            "IPV4&TCP": "tcp",
            "IPV6": "ip",
            "IPV6&UDP": "udp",
            "IPV6&TCP": "tcp",
        }

        self.dut.kill_all()
        global testQueues
        if self.nic in ["IGC-I225_LM", "IGC-I226_LM"]:
            testQueues = [2]
        # test with different rss queues
        for queue in testQueues:
            if queue == 16:
                self.pmdout.start_testpmd(
                    "all",
                    "--rxq=%d --txq=%d --rx-offloads=0x00080000 " % (queue, queue),
                    socket=self.ports_socket,
                )
            else:
                self.pmdout.start_testpmd(
                    "all",
                    "--mbcache=128 --rxq=%d --txq=%d --rx-offloads=0x00080000"
                    % (queue, queue),
                    socket=self.ports_socket,
                )

            for iptype, rsstype in list(iptypes.items()):
                self.dut.send_expect("set verbose 8", "testpmd> ")
                self.dut.send_expect("set fwd rxonly", "testpmd> ")
                self.dut.send_expect("set nbcore %d" % (queue + 1), "testpmd> ")

                out = self.dut.send_expect(
                    "port config all rss %s" % rsstype, "testpmd> "
                )
                self.verify(
                    "error" not in out,
                    "Configuration of RSS hash failed: Invalid argument",
                )

                # configure the reta with specific mappings.
                if self.nic in ["cavium_a063", "cavium_a064"]:
                    for i in range(64):
                        reta_entries.insert(i, random.randint(0, queue - 1))
                        self.dut.send_expect(
                            "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]),
                            "testpmd> ",
                        )
                elif self.nic in ["hi1822"]:
                    for i in range(256):
                        reta_entries.insert(i, random.randint(0, queue - 1))
                        self.dut.send_expect(
                            "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]),
                            "testpmd> ",
                        )
                elif self.nic in ["IXGBE_10G-82599_SFP", "IGC-I225_LM", "IGC-I226_LM"]:
                    for i in range(128):
                        reta_entries.insert(i, random.randint(0, queue - 1))
                        self.dut.send_expect(
                            "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]),
                            "testpmd> ",
                        )
                else:
                    for i in range(512):
                        reta_entries.insert(i, random.randint(0, queue - 1))
                        self.dut.send_expect(
                            "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]),
                            "testpmd> ",
                        )

                self.send_packet(itf, iptype)

            self.dut.send_expect("quit", "# ", 30)

    def test_rss_key_size(self):
        nic_rss_key_size = {
            "ICE_25G-E810C_SFP": 52,
            "ICE_25G-E823C_QSFP": 52,
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
            "IGC-I226_LM": 40,
            "IXGBE_10G-X540T": 40,
        }
        self.verify(
            self.nic in list(nic_rss_key_size.keys()),
            "Not supporte rss key on %s" % self.nic,
        )

        dutPorts = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(localPort)
        self.dut.kill_all()
        self.pmdout.start_testpmd("all", "--rxq=2 --txq=2")

        self.dut.send_expect("start", "testpmd> ", 120)
        out = self.dut.send_expect("show port info all", "testpmd> ", 120)
        self.dut.send_expect("quit", "# ", 30)

        pattern = re.compile("Hash key size in bytes:\s(\d+)")
        m = pattern.search(out)
        if m is not None:
            size = m.group(1)
            print(utils.GREEN("******************"))
            print(
                utils.GREEN(
                    "NIC %s hash size %d and expected %d"
                    % (self.nic, int(size), nic_rss_key_size[self.nic])
                )
            )
            if nic_rss_key_size[self.nic] == int(size):
                self.verify(True, "pass")
            else:
                self.verify(False, "fail")

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
