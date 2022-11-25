# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2017 Intel Corporation
#

"""
DPDK Test suite.

Test tx preparation feature

"""

import os
import random
import re
import subprocess
import time

import framework.dut as dut
from framework.config import PortConf
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import FOLDERS
from framework.test_case import TestCase

#
#
# Test class.
#

Normal_mtu = 1500
Max_mtu = 9000
TSO_value = 1460
count = 4


class TestTX_preparation(TestCase):
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.ports = self.dut.get_ports(self.nic)
        self.verify(len(self.ports) >= 1, "Insufficient number of ports.")
        self.used_dut_port = self.ports[0]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        out = self.tester.send_expect(
            "ethtool -K %s rx off tx off tso off gso\
            off gro off lro off"
            % self.tester_intf,
            "#",
        )
        if "Cannot change large-receive-offload" in out:
            self.tester.send_expect(
                "ethtool -K %s rx off tx off tso off gso\
            off gro off"
                % self.tester_intf,
                "#",
            )
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester_intf, Max_mtu), "#")

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut_testpmd = PmdOutput(self.dut)
        # use one port test the case
        self.dut_testpmd.start_testpmd(
            "Default",
            " --portmask=1 --port-topology=chained --max-pkt-len=%s --tx-offloads=0x8000"
            % Max_mtu,
        )
        self.dmac = "00:11:22:33:44:55"
        self.dut_testpmd.execute_cmd("set fwd csum")
        self.dut_testpmd.execute_cmd("set verbose 1")
        # enable ip/udp/tcp hardware checksum
        self.dut_testpmd.execute_cmd("port stop all")
        self.dut_testpmd.execute_cmd("csum set ip hw 0")
        self.dut_testpmd.execute_cmd("csum set tcp hw 0")
        self.dut_testpmd.execute_cmd("csum set udp hw 0")

    def start_tcpdump(self, rxItf):
        # only sniff form dut packet and filter lldp packet
        param = "ether[12:2]!=0x88cc and ether dst %s -Q in" % self.dmac
        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect(
            "tcpdump %s -i %s -n -e -vv -w\
            ./getPackageByTcpdump.cap 2> /dev/null& "
            % (param, rxItf),
            "#",
        )

    def get_tcpdump_package(self):
        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect(
            "tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#"
        )

    def send_packet_verify(self, tsoflag=0):
        """
        Send packet to portid and output
        """
        self.pmd_output = PmdOutput(self.dut)
        res = self.pmd_output.wait_link_status_up("all", 30)
        self.verify(res is True, "there have port link is down")

        LrgLength = random.randint(Normal_mtu, Max_mtu - 100)
        pkts = {
            "IPv4/cksum TCP": 'Ether(dst="%s")/IP()/TCP(flags=0x10)\
                    /Raw(RandString(50))'
            % self.dmac,
            "IPv4/bad IP cksum": 'Ether(dst="%s")/IP(chksum=0x1234)\
                    /TCP(flags=0x10)/Raw(RandString(50))'
            % self.dmac,
            "IPv4/bad TCP cksum": 'Ether(dst="%s")/IP()/TCP(flags=0x10,\
                    chksum=0x1234)/Raw(RandString(50))'
            % self.dmac,
            "IPv4/large pkt": 'Ether(dst="%s")/IP()/TCP(flags=0x10)\
                    /Raw(RandString(%s))'
            % (self.dmac, LrgLength),
            "IPv4/bad cksum/large pkt": 'Ether(dst="%s")/IP(chksum=0x1234)\
                    /TCP(flags=0x10,chksum=0x1234)/Raw(RandString(%s))'
            % (self.dmac, LrgLength),
            "IPv6/cksum TCP": 'Ether(dst="%s")/IPv6()/TCP(flags=0x10)\
                    /Raw(RandString(50))'
            % self.dmac,
            "IPv6/cksum UDP": 'Ether(dst="%s")/IPv6()/UDP()\
                    /Raw(RandString(50))'
            % self.dmac,
            "IPv6/bad TCP cksum": 'Ether(dst="%s")/IPv6()/TCP(flags=0x10,\
                    chksum=0x1234)/Raw(RandString(50))'
            % self.dmac,
            "IPv6/large pkt": 'Ether(dst="%s")/IPv6()/TCP(flags=0x10)\
                    /Raw(RandString(%s))'
            % (self.dmac, LrgLength),
        }

        for packet_type in list(pkts.keys()):
            self.start_tcpdump(self.tester_intf)
            self.tester.scapy_append(
                'sendp([%s], iface="%s", count=%d)'
                % (pkts[packet_type], self.tester_intf, count)
            )
            self.tester.scapy_execute()
            out = self.get_tcpdump_package()
            if packet_type == "IPv6/cksum UDP":
                self.verify(
                    "udp sum ok" in out, "Failed to check UDP checksum correctness!!!"
                )
            else:
                self.verify("cksum" in out, "Failed to check IP/TCP checksum!!!")
                self.verify(
                    "correct" in out and "incorrect" not in out,
                    "Failed to check IP/TCP/UDP checksum correctness!!!",
                )

            if tsoflag == 1:
                if packet_type in [
                    "IPv4/large pkt",
                    "IPv6/large pkt",
                    "IPv4/bad cksum/large pkt",
                ]:
                    segnum = int(LrgLength / TSO_value)
                    LastLength = LrgLength % TSO_value
                    num = out.count("length %s" % TSO_value)
                    self.verify(
                        "length %s" % TSO_value in out and num == segnum * count,
                        "Failed to verify TSO correctness for large packets!!!",
                    )
                    if LastLength != 0:
                        num = out.count("length %s:" % LastLength)
                        self.verify(
                            "length %s" % LastLength in out and num == count,
                            "Failed to verify TSO correctness for large packets!!!",
                        )

    def test_tx_preparation_NonTSO(self):
        """
        ftag functional test
        """
        self.dut_testpmd.execute_cmd("tso set 0 0")
        self.dut_testpmd.execute_cmd("port start all")
        self.dut_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.dut_testpmd.execute_cmd("start")

        self.send_packet_verify()

    def test_tx_preparation_TSO(self):
        """
        ftag functional test
        """
        self.dut_testpmd.execute_cmd("tso set %s 0" % TSO_value)
        self.dut_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.dut_testpmd.execute_cmd("port start all")
        self.dut_testpmd.execute_cmd("start")

        self.send_packet_verify(1)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut_testpmd.execute_cmd("stop")
        self.dut_testpmd.quit()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.tester.send_expect(
            "ifconfig %s mtu %s" % (self.tester_intf, Normal_mtu), "#"
        )
        self.dut.kill_all()
