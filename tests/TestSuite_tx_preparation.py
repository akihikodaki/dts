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

Test tx preparation feature

"""

import os
import time
import dut
import re
import subprocess
from config import PortConf
from test_case import TestCase
from pmd_output import PmdOutput
from settings import FOLDERS
from packet import Packet
import random
#
#
# Test class.
#

Normal_mtu = 1500
Max_mtu = 9000
TSO_value = 1460


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
        out = self.tester.send_expect("ethtool -K %s rx off tx off tso off gso\
            off gro off lro off" %self.tester_intf, "#") 
        if "Cannot change large-receive-offload" in out:
            self.tester.send_expect("ethtool -K %s rx off tx off tso off gso\
            off gro off" %self.tester_intf, "#")
        self.tester.send_expect("ifconfig %s mtu %s" 
            %(self.tester_intf, Max_mtu), "#")

         
    def set_up(self):
        """
        Run before each test case.
        """
        self.dut_testpmd = PmdOutput(self.dut)
        # use one port test the case
        self.dut_testpmd.start_testpmd(
                "Default", " --portmask=1 --port-topology=chained --max-pkt-len=%s" %Max_mtu)
        self.dmac = self.dut_testpmd.get_port_mac(0)
        self.dut_testpmd.execute_cmd('set fwd csum')
        self.dut_testpmd.execute_cmd('set verbose 1')
        #enable ip/udp/tcp hardware checksum
        self.dut_testpmd.execute_cmd('csum set ip hw 0')
        self.dut_testpmd.execute_cmd('csum set tcp hw 0')
        self.dut_testpmd.execute_cmd('csum set udp hw 0')

    def start_tcpdump(self, rxItf):
        # only sniff form dut packet and filter lldp packet
        param = "ether[12:2]!=0x88cc and ether src %s" % self.dmac
        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump %s -i %s -n -e -vv -w\
            ./getPackageByTcpdump.cap 2> /dev/null& " % (param,rxItf), "#")

    def get_tcpdump_package(self):
        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect(
            "tcpdump -nn -e -v -r ./getPackageByTcpdump.cap", "#")

    def send_packet_verify(self, tsoflag = 0):
        """
        Send packet to portid and output
        """
        LrgLength = random.randint(Normal_mtu, Max_mtu-100)
        pkts = {'IPv4/cksum TCP': 'Ether(dst="%s")/IP()/TCP(flags=0x10)\
                    /Raw(RandString(50))' % self.dmac,
                'IPv4/bad IP cksum': 'Ether(dst="%s")/IP(chksum=0x1234)\
                    /TCP(flags=0x10)/Raw(RandString(50))' %self.dmac,
                'IPv4/bad TCP cksum': 'Ether(dst="%s")/IP()/TCP(flags=0x10,\
                    chksum=0x1234)/Raw(RandString(50))' %self.dmac,
                'IPv4/large pkt': 'Ether(dst="%s")/IP()/TCP(flags=0x10)\
                    /Raw(RandString(%s))' %(self.dmac, LrgLength),
                'IPv4/bad cksum/large pkt': 'Ether(dst="%s")/IP(chksum=0x1234)\
                    /TCP(flags=0x10,chksum=0x1234)/Raw(RandString(%s))'  
                    %(self.dmac, LrgLength),
                'IPv6/cksum TCP': 'Ether(dst="%s")/IPv6()/TCP(flags=0x10)\
                    /Raw(RandString(50))' %self.dmac,
                'IPv6/cksum UDP': 'Ether(dst="%s")/IPv6()/UDP()\
                    /Raw(RandString(50))' %self.dmac,
                'IPv6/bad TCP cksum': 'Ether(dst="%s")/IPv6()/TCP(flags=0x10,\
                    chksum=0x1234)/Raw(RandString(50))' %self.dmac,
                'IPv6/large pkt': 'Ether(dst="%s")/IPv6()/TCP(flags=0x10)\
                    /Raw(RandString(%s))' %(self.dmac, LrgLength) } 

        for packet_type in pkts.keys():
            self.start_tcpdump(self.tester_intf)
            self.tester.scapy_append(
                'sendp([%s], iface="%s")' % (pkts[packet_type], self.tester_intf))
            self.tester.scapy_execute()
            out = self.get_tcpdump_package()
            if packet_type == 'IPv6/cksum UDP':
                self.verify("udp sum ok" in out, 
                    "Failed to check UDP checksum correctness!!!")
            else :
                self.verify("cksum" in out, "Failed to check IP/TCP checksum!!!")
                self.verify("correct" in out and "incorrect" not in out, 
                    "Failed to check IP/TCP/UDP checksum correctness!!!")

            if tsoflag == 1:
                 if packet_type in\
                    ['IPv4/large pkt', 'IPv6/large pkt', 'IPv4/bad cksum/large pkt']:
                    segnum = LrgLength / TSO_value 
                    LastLength = LrgLength % TSO_value
                    num = out.count('length %s' %TSO_value)
                    self.verify("length %s" %TSO_value in out and num == segnum,
                        "Failed to verify TSO correctness for large packets!!!")
                    if LastLength != 0 :
                        num = out.count('length %s' %LastLength)
                        self.verify("length %s" %LastLength in out and num == 1 , 
                        "Failed to verify TSO correctness for large packets!!!")
    

    def test_tx_preparation_NonTSO(self):
        """
        ftag functional test
        """
        self.dut_testpmd.execute_cmd('tso set 0 0')
        self.dut_testpmd.execute_cmd('start')

        self.send_packet_verify()
        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.quit() 
 
    def test_tx_preparation_TSO(self):
        """
        ftag functional test
        """
        self.dut_testpmd.execute_cmd('tso set %s 0' %TSO_value)
        self.dut_testpmd.execute_cmd('start')

        self.send_packet_verify(1)
        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.quit()


    def tear_down(self):
        """
        Run after each test case. 
        """ 
        pass

        
    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.tester.send_expect("ifconfig %s mtu %s" 
            %(self.tester_intf, Normal_mtu), "#")
        self.dut.kill_all() 
