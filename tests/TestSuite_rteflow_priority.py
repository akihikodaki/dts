# BSD LICENSE
#
# Copyright(c) 2019 Intel Corporation. All rights reserved.
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

Test rte_flow priority
"""

import re
import time
import string
from time import sleep
from scapy.utils import struct, socket, PcapWriter

import utils
from test_case import TestCase
from settings import HEADER_SIZE
from pmd_output import PmdOutput
import sys
import imp
imp.reload(sys)


class TestRteflowPriority(TestCase):
    
    def set_up_all(self):
        """
        Run at the start of each test suite.

        PMD prerequisites.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.__tx_iface = self.tester.get_interface(localPort)
        cores = self.dut.get_core_list("1S/5C/1T")
        self.coreMask = utils.create_mask(cores)
        self.portMask = utils.create_mask([self.dut_ports[0]])
        self.path = self.dut.apps_name['test-pmd']
    
    def set_up(self):
        """
        Run before each test case.
        """
        pass
    #
    # Utility methods and other non-test code.
    #
    ###########################################################################
    scapyCmds = []  

    def check_link(self):
        # check status in test case, dut and tester both should be up.
        self.pmd_output = PmdOutput(self.dut)
        res = self.pmd_output.wait_link_status_up('all', timeout=30)
        if res is True:
            for i in range(15):
                out = self.tester.get_port_status(self.dut_ports[0])
                if out == 'up':
                    break
                else:
                    time.sleep(1)
            return True
        else:
            return False

    def send_pkt(self, cmd):
        """
        Send packages and verify behavior.
        """
        self.tester.scapyCmds.append(cmd)
        self.tester.scapy_execute()
        
    def get_packet_number(self, out, match_string):
        """
        get the rx packets number.
        """

        out_lines=out.splitlines()
        pkt_num=0
        for i in range(len(out_lines)):
            if match_string in out_lines[i]:
                result_scanner=(r'RX-packets:\s?(\d+)')
                scanner=re.compile(result_scanner,re.DOTALL)
                m=scanner.search(out_lines[i+1])
                pkt_num=int(m.group(1))
                break
        return pkt_num

    def check_queue_rx_packets_number(self, out, queue_id):
        """
        check the queue rx packets number.
        """
        match_string="------- Forward Stats for RX Port= 0/Queue= %d" % queue_id
        pkt_num=self.get_packet_number(out, match_string)
        return pkt_num
    # 
    # test cases.
    #
    ###########################################################################

    def test_priority_in_pipeline_mode(self):
        """
        priority is active in pipeline mode.
        """
        #start testpmd in pipeline mode
        # genarate eal
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=1 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)
        
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd> ", 15)
        
        #create fdir and switch rules with different priority 
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 1 / end ", "testpmd>", 15)
        self.verify("Successed" and "(2)" in out, "failed: rule map to wrong filter")
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 25 dst is 23 / end actions queue index 2 / end ", "testpmd>", 15)
        self.verify("Successed" and "(2)" in out, "failed: rule map to wrong filter")
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.4 dst is 192.168.0.7 tos is 4 ttl is 20 / tcp src is 25 dst is 23 / end actions queue index 3 / end ", "testpmd>", 15)
        self.verify("Successed" and "(1)" in out, "failed: rule map to wrong filter")
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 / udp / vxlan / eth / ipv4 src is 192.168.0.4 dst is 192.168.0.7 / udp src is 25 dst is 23 / end actions queue index 4 / end ", "testpmd>", 15)
        self.verify("Successed" and "(1)" in out, "failed: rule map to wrong filter")
        out = self.dut.send_expect("flow list 0", "testpmd> ", 15)
        self.logger.info(out)
        self.verify( "3" in out, "failed: flow rules created error")

        #send pkts and check the rules are written to different filter tables and the rules can work
        self.dut.send_expect("start", "testpmd>", 20)
        a=self.check_link()
        self.verify(a, "failed: link can not up")
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:66")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 1)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 1') 
        
        self.dut.send_expect("start", "testpmd>", 20)
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:66")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/UDP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 2)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 2')
        
        self.dut.send_expect("start", "testpmd>", 20)
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:66")/IP(src="192.168.0.4",dst="192.168.0.7",tos=4,ttl=20)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 3)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 3')
 
        self.dut.send_expect("start", "testpmd>", 20)
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:66")/IP()/UDP()/VXLAN()/Ether()/IP(src="192.168.0.4",dst="192.168.0.7")/UDP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 4)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 4')

        #create rules without priority, only the pattern supported by switch can be created.
        out= self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 src is 192.168.1.2 dst is 192.168.0.3 tos is 5 / tcp src is 25 dst is 23 / end actions queue index 1 / end ", "testpmd>", 15)
        self.verify( "Failed" not in out, "failed: default priority 0 is not work")
        out=self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 ttl is 20 / sctp src is 25 dst is 23 / end actions queue index 1 / end ", "testpmd>", 15)
        self.verify( "Failed" in out, "failed: pattern only support by fdir can not be created in default priority")

        self.dut.send_expect("flow flush 0", "testpmd>", 20)
        self.dut.send_expect("quit", "#", 50)

    def test_priority_in_nonpipeline_mode(self):
        """
        priority is not active in pipeline mode.
        """
        
        #start testpmd without pipeline-mode-support parameter, check the testpmd is launch in non-pipeline mode
        command = self.path + '-c %s -n 4 -w %s --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)
        
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end", "testpmd>", 15)       
        self.verify( "Successed" and "(1)" in out, "failed: rule can't be created to fdir")
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end", "testpmd>", 15)       
        self.verify( "Failed" in out, "failed: default value of priority is 0 in non-pipeline mode")
        self.dut.send_expect("flow flush 0", "testpmd>", 20)
        self.dut.send_expect("quit", "#", 50)
        
        #restart testpmd with pipeline-mode-support=0, check the testpmd is launch in non-pipeline mode
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=0 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)
        
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end", "testpmd>", 15)       
        self.verify( "Successed" and "(1)" in out, "failed: rule can't be created to fdir")
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 2 / end", "testpmd>", 15)       
        self.verify( "Failed" in out, "failed: default value of priority is 0 in non-pipeline mode")
        self.dut.send_expect("flow flush 0", "testpmd>", 20)
        self.dut.send_expect("quit", "#", 50)

    def test_no_destination_high_prority(self):
        """
        no destination high priority rule is not acceptable.
        """
        
        #start testpmd in pipeline mode
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=1 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)
        
        #create no destination high priority rules, check the rules can not be created.
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions / end", "testpmd>", 15)       
        self.verify( "Bad argument" in out, "failed: no destination high priority rule is not acceptable")
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end", "testpmd>", 15)       
        self.verify( "Bad argument" in out, "failed: no destination high priority rule is not acceptable")
        self.dut.send_expect("quit", "#", 50)

    def test_create_fdir_rule_with_priority_0(self):
        """
        create a rule only supported by fdir filter with priority 0 is not acceptable.
        """
        
        #start testpmd in pipeline mode
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=1 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)

        #create rules only supported by fdir with priority 0, check the rules can not be created.
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv6 src is 1111:2222:3333:4444:5555:6666:7777:8888 dst is 1111:2222:3333:4444:5555:6666:7777:9999 / sctp src is 25 dst is 23 / end actions queue index 1 / end", "testpmd>", 15)       
        self.verify( "Failed" in out, "failed: priority is not work")
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 ttl is 20 / sctp src is 25 dst is 23 / end actions queue index 1 / end", "testpmd>", 15)       
        self.verify( "Failed" in out, "failed: priority is not work")
        self.dut.send_expect("quit", "#", 50)

    def test_create_switch_rule_with_priority_1(self):
        """
        create a rule only supported by switch filter with priority 1 is not acceptable.
        """
        
        #start testpmd in pipeline mode
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=1 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)

        #create rules only supported by switch with priority 1, check the rules can not be created.
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / end actions queue index 3 / end", "testpmd>", 15)       
        self.verify( "Failed" in out, "failed: priority is not work")
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 / nvgre / eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / udp src is 25 dst is 23 / end actions queue index 3 / end", "testpmd>", 15)       
        self.verify( "Failed" in out, "failed: priority is not work")
        self.dut.send_expect("quit", "#", 50)

    def test_rules_with_same_parameters_different_action(self):
        """
        it's acceptable to create same rules with different filter in pipeline mode.
        """

        #start testpmd in pipeline mode
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=1 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)

        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)


        #create rules with same parameters but different action
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 1 / end", "testpmd>", 15)       
        self.verify( "Successed" and "(2)" in out, "failed: switch rule can't be created")
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 3 / end", "testpmd>", 15)       
        self.verify( "Successed" and "(1)" in out, "failed: fdir rule can't be created")
        
        #send a pkt to check the switch rule is work for its high priority
        self.dut.send_expect("start", "testpmd>", 20)
        a=self.check_link()
        self.verify(a, "failed: link can not up")

        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:01")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 1)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 1')
        
        #remove the switch rule and check the fdir rule is work
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd>", 15)
        self.dut.send_expect("start", "testpmd>", 20)
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:02")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 3)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 3')

        self.dut.send_expect("flow flush 0", "testpmd>", 15)
        self.dut.send_expect("quit", "#", 50)

        #restart testpmd in pipeline mode
        command = self.path + '-c %s -n 4 -w %s,pipeline-mode-support=1 --log-level="ice,7" -- -i --portmask=%s --rxq=10 --txq=10' % (self.coreMask, self.dut.ports_info[0]['pci'], utils.create_mask([self.dut_ports[0]]))
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)

        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

        #create rules with same parameters but different action
        out=self.dut.send_expect("flow create 0 priority 1 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 3 / end", "testpmd>", 15)       
        self.verify( "Successed" and "(1)" in out, "failed: fdir rule can't be created")
        out=self.dut.send_expect("flow create 0 priority 0 ingress pattern eth / ipv4 src is 192.168.0.2 dst is 192.168.0.3 tos is 4 / tcp src is 25 dst is 23 / end actions queue index 1 / end", "testpmd>", 15)       
        self.verify( "Successed" and "(2)" in out, "failed: switch rule can't be created")
        
        #send a pkt to check the switch rule is work for its high priority
        self.dut.send_expect("start", "testpmd>", 20)
        a=self.check_link()
        self.verify(a, "failed: link can not up")
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:01")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 1)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 1')

        #remove the switch rule and check the fdir rule is work
        self.dut.send_expect("flow destroy 0 rule 1", "testpmd>", 15)
        self.dut.send_expect("start", "testpmd>", 20)
        self.send_pkt('sendp([Ether(dst="00:00:00:00:01:00",src="11:22:33:44:55:02")/IP(src="192.168.0.2",dst="192.168.0.3",tos=4)/TCP(sport=25,dport=23)/Raw("x"*80)],iface="%s")'%(self.__tx_iface))
        out=self.dut.send_expect("stop", "testpmd>", 20)
        pkt_num=self.check_queue_rx_packets_number(out, 3)
        self.verify(pkt_num==1, "failed: the flow rule can not work")
        self.logger.info('pass: queue id is 3')

        self.dut.send_expect("flow flush 0", "testpmd>", 20)
        self.dut.send_expect("quit", "#", 50)
    # 
    ###########################################################################

    def tear_down_all(self):
        pass

    def tear_down(self):
        self.dut.kill_all()
        
    




        





