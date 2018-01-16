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

Test the support of VLAN Offload Features by Poll Mode Drivers.

"""

import utils
import time
import re

from test_case import TestCase
from settings import HEADER_SIZE
from pmd_output import PmdOutput
from settings import DRIVERS

from project_dpdk import DPDKdut
from dut import Dut
from packet import Packet


class TestQueue_region(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Queue region Prerequistites
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortpark_TLV"], "NIC Unsupported: " + str(self.nic))

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_intf = self.tester.get_interface(localPort)
        self.tester_mac = self.tester.get_mac(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pmdout = PmdOutput(self.dut)
        self.cores = "1S/4C/1T"
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=16 --txq=16")
        self.dut.send_expect("port config all rss all", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def get_queue_number(self):
        """
        get the queue which packet enter.
        """
        outstring = self.dut.send_expect("stop", "testpmd> ")
        result_scanner = r"Forward Stats for RX Port= %s/Queue=\s?([0-9]+)" % self.dut_ports[0]
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        queue_id = m.group(1)
        print "queue is %s" % queue_id
        self.dut.send_expect("start", "testpmd> ")
        return queue_id

    def send_and_check(self, queue_region, mac, pkt_type="udp", frag=0, prio=None, flags=None, tag=None, ethertype=None):
        """
        send packet and check the result
        """
        if prio is None:
            self.send_packet_pctype(mac, pkt_type, frag, flags, tag, ethertype)
        else:
            self.send_packet_up(mac, pkt_type, prio)
        queue = self.get_queue_number()
        self.verify(queue in queue_region, "the packet doesn't enter the expected queue region.")

    def send_packet_pctype(self, mac, pkt_type="udp", frag=0, flags=None, tag=None, ethertype=None):
        """
        send different PCTYPE packets.
        """
        if (pkt_type == "udp"):
            pkt = Packet(pkt_type='UDP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
        elif (pkt_type == "tcp"):
            pkt = Packet(pkt_type='TCP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('tcp', {'flags': flags})
        elif (pkt_type == "sctp"):
            pkt = Packet(pkt_type='SCTP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('sctp', {'tag': tag})
        elif (pkt_type == "ipv4"):
            pkt = Packet(pkt_type='IP_RAW')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('ipv4', {'frag': frag})
        elif (pkt_type == "ipv6_udp"):
            pkt = Packet(pkt_type='IPv6_UDP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
        elif (pkt_type == "ipv6_tcp"):
            pkt = Packet(pkt_type='IPv6_TCP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            if (self.nic in ["fortpark_TLV"]):
                pkt.config_layer('tcp', {'flags': flags})
        elif (pkt_type == "ipv6_sctp"):
            pkt = Packet(pkt_type='IPv6_SCTP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('sctp', {'tag': tag})
        elif (pkt_type == "ipv6"):
            pkt = Packet()
            pkt.assign_layers(['ether', 'ipv6', 'raw'])
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
        elif (pkt_type == "L2"):
            pkt = Packet()
            pkt.assign_layers(['ether', 'raw'])
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac, 'type': ethertype})
        pkt.send_pkt(tx_port=self.tester_intf)

    def send_packet_up(self, mac, pkt_type="udp", prio=0):
        """
        send different User Priority packets.
        """
        if (pkt_type == "ipv4"):
            pkt = Packet()
            pkt.assign_layers(['ether', 'vlan', 'ipv4', 'raw'])
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('vlan', {'vlan': 0, 'prio': prio})
        elif (pkt_type == "udp"):
            pkt = Packet(pkt_type='VLAN_UDP')
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('vlan', {'vlan': 0, 'prio': prio})
        elif (pkt_type == "tcp"):
            pkt = Packet()
            pkt.assign_layers(['ether', 'vlan', 'ipv4', 'tcp', 'raw'])
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('vlan', {'vlan': 0, 'prio': prio})
        elif (pkt_type == "ipv6_udp"):
            pkt = Packet()
            pkt.assign_layers(['ether', 'vlan', 'ipv6', 'udp', 'raw'])
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('vlan', {'vlan': 0, 'prio': prio})
        pkt.send_pkt(tx_port=self.tester_intf)

    def get_and_compare_rules(self, out, QueueRegion_num, FlowType_num, UP_num):
        """
        dump all queue region rules that have been created in memory and compare that total rules number with the given expected number
        to see if they are equal, as to get your conclusion after you have deleted any queue region rule entry.
        """
        self.verify("error" not in out, "the queue region settings has error.")
        actual_QRnum = re.findall("region_id.*", out)
        actual_FTnum = re.findall("flowtype_num\D*(\d*).*", out)
        actual_UPnum = re.findall("user_priority_num\D*(\d*).*", out)
        actual_flowtypenum = 0
        actual_UserPrioritynum = 0
        self.verify(len(actual_QRnum) == QueueRegion_num, "the queue-region number count error")
        for i in range(len(actual_FTnum)):
            actual_flowtypenum += int(actual_FTnum[i])
        self.verify(actual_flowtypenum == FlowType_num, "the flowtype number count error")
        for i in range(len(actual_UPnum)):
            actual_UserPrioritynum += int(actual_UPnum[i])
        self.verify(actual_UserPrioritynum == UP_num, "the UP number count error")

    def test_pctype_map_queue_region(self):
        # clear the environment
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        # set queue region on a port
        self.dut.send_expect("set port 0 queue-region region_id 0 queue_start_index 1 queue_num 1", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 1 queue_start_index 3 queue_num 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 2 queue_start_index 6 queue_num 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 3 queue_start_index 8 queue_num 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 4 queue_start_index 11 queue_num 4", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 5 queue_start_index 15 queue_num 1", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 6 queue_start_index 2 queue_num 1", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 7 queue_start_index 10 queue_num 1", "testpmd> ")

        # Set the mapping of flowtype to region index on a port
        self.dut.send_expect("set port 0 queue-region region_id 0 flowtype 31", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 1 flowtype 32", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 2 flowtype 33", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 3 flowtype 34", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 4 flowtype 35", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 6 flowtype 36", "testpmd> ")

        # the default UDP packet configuration of fortpark is not consistent with fortville
        if(self.nic in ["fortpark_TLV"]):
            self.dut.send_expect("set port 0 queue-region region_id 2 flowtype 39", "testpmd> ")
        else:
            self.dut.send_expect("set port 0 queue-region region_id 2 flowtype 41", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 3 flowtype 43", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 4 flowtype 44", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 5 flowtype 45", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 7 flowtype 46", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 1 flowtype 63", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")

        # send the packets and verify the results
        queue_region = ["1"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="udp")

        # fortville can't parse the TCP SYN type packet, fortpark can parse it.
        # but you need to update hardware defined pctype to software defined
        # flow type mapping table manully.
        if(self.nic in ["fortpark_TLV"]):
            self.dut.send_expect("port config 0 pctype mapping update 32 1", "testpmd> ")
            self.dut.send_expect("port config all rss 1", "testpmd> ")
            queue_region = ["3", "4"]
            self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="tcp", flags="S")
            self.dut.send_expect("port config all rss all", "testpmd> ")
        else:
            queue_region = ["6", "7"]
            self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="tcp", flags="S")

        queue_region = ["6", "7"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="tcp", flags="PA")

        queue_region = ["8", "9"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="sctp", tag=1)

        queue_region = ["11", "12", "13", "14"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv4")

        queue_region = ["2"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv4", frag=1)

        queue_region = ["8", "9"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv6_tcp", flags="PA")

        queue_region = ["11", "12", "13", "14"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv6_sctp", tag=2)

        queue_region = ["6", "7"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv6_udp")

        queue_region = ["15"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv6")

        queue_region = ["3", "4"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="L2", ethertype=0x88bb)

        queue_region = ["11", "12", "13", "14"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv4", prio=1)

        # clear all the queue region configuration
        # check if there is 1 flow rule have been created
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 8, 12, 0)
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 0, 0, 0)

    def test_up_map_queue_region(self):
        # clear the environment
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        # set queue region on a port
        self.dut.send_expect("set port 0 queue-region region_id 0 queue_start_index 0 queue_num 1", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 6 queue_start_index 1 queue_num 8", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 2 queue_start_index 10 queue_num 4", "testpmd> ")

        # Set the mapping of user priority to region index on a port
        self.dut.send_expect("set port 0 queue-region UP 3 region_id 0", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region UP 1 region_id 6", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region UP 2 region_id 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region UP 7 region_id 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")

        # send the packets and verify the results
        queue_region = ["0"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="udp", prio=3)

        queue_region = ["1", "2", "3", "4", "5", "6", "7", "8"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="ipv6_udp", prio=1)

        queue_region = ["10", "11", "12", "13"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="tcp", prio=2)

        queue_region = ["10", "11", "12", "13"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="tcp", prio=7)

        queue_region = ["10", "11", "12", "13"]
        self.send_and_check(queue_region, mac=self.pf_mac, pkt_type="udp", prio=7)

        self.send_packet_pctype(mac=self.pf_mac, pkt_type="udp")
        queue = self.get_queue_number()
        self.verify(queue not in ["10", "11", "12", "13"], "the packet doesn't enter the expected queue.")

        # clear all the queue region configuration
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 3, 0, 4)
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 0, 0, 0)

        # confirm packet can't into the previous queue_region
        self.send_packet_up(mac=self.pf_mac, pkt_type="udp", prio=7)
        queue = self.get_queue_number()
        self.verify(queue not in ["10", "11", "12", "13"], "the queue regions have not been flushed clearly.")

    def test_boundary_values(self):
        # boundary value testing of "Set a queue region on a port"
        # clear the environment
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        # the following parameters can be set successfully
        outstring = self.dut.send_expect("set port 0 queue-region region_id 0 queue_start_index 0 queue_num 16", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        outstring = self.dut.send_expect("set port 0 queue-region region_id 0 queue_start_index 15 queue_num 1", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        outstring = self.dut.send_expect("set port 0 queue-region region_id 7 queue_start_index 2 queue_num 8", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        # the following parameters failed to be set.
        # region_id can be set to 0-7
        self.dut.send_expect("set port 0 queue-region region_id 8 queue_start_index 2 queue_num 2", "error")
        self.dut.send_expect("set port 0 queue-region region_id 1 queue_start_index 16 queue_num 1", "error")
        self.dut.send_expect("set port 0 queue-region region_id 2 queue_start_index 15 queue_num 2", "error")
        self.dut.send_expect("set port 0 queue-region region_id 3 queue_start_index 2 queue_num 3", "error")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 0, 0, 0)
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        # boundary value testing of "Set the mapping of flowtype to region index on a port"
        self.dut.send_expect("set port 0 queue-region region_id 0 queue_start_index 2 queue_num 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 7 queue_start_index 4 queue_num 4", "testpmd> ")

        # the following parameters can be set successfully
        outstring = self.dut.send_expect("set port 0 queue-region region_id 0 flowtype 63", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")
        outstring = self.dut.send_expect("set port 0 queue-region region_id 7 flowtype 0", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")

        # the following parameters failed to be set.
        self.dut.send_expect("set port 0 queue-region region_id 0 flowtype 64", "error")
        self.dut.send_expect("set port 0 queue-region region_id 2 flowtype 34", "error")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 2, 2, 0)
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

        # boundary value testing of "Set the mapping of UP to region index on a port"
        self.dut.send_expect("set port 0 queue-region region_id 0 queue_start_index 2 queue_num 2", "testpmd> ")
        self.dut.send_expect("set port 0 queue-region region_id 7 queue_start_index 4 queue_num 4", "testpmd> ")

        # the following parameters can be set successfully
        # UP value can be set to 0-7
        outstring = self.dut.send_expect("set port 0 queue-region UP 7 region_id 0", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")
        outstring = self.dut.send_expect("set port 0 queue-region UP 0 region_id 7", "testpmd> ")
        self.verify("error" not in outstring, "boundary value check failed")

        # the following parameters failed to be set.
        self.dut.send_expect("set port 0 queue-region UP 8 region_id 0", "error")
        self.dut.send_expect("set port 0 queue-region UP 1 region_id 2", "error")
        self.dut.send_expect("set port 0 queue-region flush on", "testpmd> ")
        out = self.dut.send_expect("show port 0 queue-region", "testpmd> ")
        self.get_and_compare_rules(out, 2, 0, 2)
        self.dut.send_expect("set port 0 queue-region flush off", "testpmd> ")

    def tear_down(self):
        """
        Run after each test case.
        """

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.kill_all()
