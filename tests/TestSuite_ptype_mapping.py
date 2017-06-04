# BSD LICENSE
#
# Copyright(c) 2017 Intel Corporation. All rights reserved.
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


import utils
from test_case import TestCase
from exception import VerifyFailure
from pmd_output import PmdOutput
from packet import Packet
import time
import re

class TestPtype_Mapping(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(self.nic in ['fortville_eagle', 'fortville_spirit',
            'fortville_spirit_single', 'fortville_25g'], 
            'ptype mapping test can not support %s nic' % self.nic)
        ports = self.dut.get_ports()
        self.verify(len(ports) >= 1, "Insufficient ports for testing")  
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        self.dut_port = valports[0]
        tester_port = self.tester.get_local_port(self.dut_port)
        self.tester_iface = self.tester.get_interface(tester_port)
        self.dut.send_expect("sed -i -e '/mb->vlan_tci, mb->vlan_tci_outer);" +\
            "/a\printf(\" - pktype: 0x%x\", mb->packet_type);'" +\
            " app/test-pmd/rxonly.c", "# ", 30)
        self.dut.build_install_dpdk(self.dut.target)
        

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_testpmd.start_testpmd("Default", "--port-topology=chained")
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')


    def run_test(self, sw_ptype, pkt_types, chk_types):
        """
        Generate and send packet according to packet type, detect each packet 
        layer.
        """
        for pkt_type in pkt_types.keys():
            if chk_types != None:
                pkt_names = chk_types[pkt_type]
            else:
                pkt_names = pkt_types[pkt_type]
            pkt = Packet(pkt_type=pkt_type)
            pkt.send_pkt(tx_port=self.tester_iface)
            out = self.dut.get_session_output(timeout=2)
            self.verify(sw_ptype in out,
                "Failed to detect correct ptype value")
            for pkt_layer_name in pkt_names:
                if pkt_layer_name not in out:
                    print utils.RED("Fail to detect %s" % pkt_layer_name)
                    raise VerifyFailure("Failed to detect %s" % pkt_layer_name)            
            print utils.GREEN("Detected %s successfully" % pkt_type)
    
    def strip_ptype(self, table, hw_ptype):
        """
        Strip software packet type from packet mapping table.
        Input: packet mapping table, hardware ptype
        Out: 32 bits software ptype or none
        """
        pattern = r"\s(%s)\s0x(0*)([1-9a-f][0-9a-f]*)" %hw_ptype
        s = re.compile(pattern)
        res = s.search(table)
        if res is None:
            print utils.RED("search none ptype")
            return None
        else:
            ptype = res.group(3)
            return ptype
        
    def run_ptype_test(self, hw_ptype, check_ptype):
        """
        Get ptype mapping table and run ptype test.
        """
        out = self.dut_testpmd.execute_cmd('ptype mapping get 0 0')
        time.sleep(3)
        self.verify("255" in out,
            "Failed to get 255 items ptype mapping table!!!")
        out = self.dut_testpmd.execute_cmd('ptype mapping get 0 1')
        time.sleep(3)
        self.verify("166" in out,
            "Failed to get 166 items ptype mapping table!!!")
        sw_ptype = self.strip_ptype(out, hw_ptype)
        if hw_ptype == 38:
            pktType = {
                "MAC_IP_IPv6_UDP_PKT":  
                    ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN",
                     "TUNNEL_IP", "INNER_L3_IPV6_EXT_UNKNOWN",
                     "INNER_L4_UDP"]
            }
        elif hw_ptype == 75:
            pktType = {
                "MAC_IP_NVGRE_MAC_VLAN_IP_PKT": 
                    ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN",
                     "TUNNEL_GRENAT", "INNER_L2_ETHER_VLAN",
                     "INNER_L3_IPV4_EXT_UNKNOWN", "INNER_L4_NONFRAG"]
            }       
        self.run_test(sw_ptype, pktType, check_ptype)
    
    def ptype_mapping_test(self, check_ptype = None):
    
        self.run_ptype_test(hw_ptype = 38, check_ptype = check_ptype)
        self.run_ptype_test(hw_ptype = 75, check_ptype = check_ptype)


    def test_ptype_mapping_get(self):
        """
        Get hardware defined ptype to software defined ptype mapping items.
        """
        self.ptype_mapping_test()
     
    def test_ptype_mapping_reset(self):
        """
        Reset packet mapping table after changing table.
        """
        self.ptype_mapping_test()
        self.dut_testpmd.execute_cmd('ptype mapping update 0 38 0x026010e1')
        chk_types = {
            "MAC_IP_IPv6_UDP_PKT":
                ["L2_ETHER", "L3_IPV6_EXT_UNKNOWN", "TUNNEL_IP",
                 "INNER_L3_IPV6_EXT_UNKNOWN", "INNER_L4_UDP"],
            "MAC_IP_NVGRE_MAC_VLAN_IP_PKT":
                ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN", "TUNNEL_GRENAT",
                 "INNER_L2_ETHER_VLAN", "INNER_L3_IPV4_EXT_UNKNOWN",
                 "INNER_L4_NONFRAG"]
        }
        self.ptype_mapping_test(check_ptype = chk_types)
        self.dut_testpmd.execute_cmd('ptype mapping reset 0')
        self.ptype_mapping_test()

    def test_ptype_mapping_update(self):
        """
        Update a specific hardware ptype's software ptype as a new one.
        """
        self.ptype_mapping_test()

        self.dut_testpmd.execute_cmd('ptype mapping update 0 38 0x026010e1')
        self.dut_testpmd.execute_cmd('ptype mapping update 0 75 0x026010e1')
        check_types = ["L2_ETHER", "L3_IPV6_EXT_UNKNOWN", "TUNNEL_IP",
                       "INNER_L3_IPV6_EXT_UNKNOWN", "INNER_L4_UDP"]

        chk_types = { 
            "MAC_IP_IPv6_UDP_PKT":           check_types,
            "MAC_IP_NVGRE_MAC_VLAN_IP_PKT":  check_types
        }
        self.ptype_mapping_test(check_ptype = chk_types)
        self.dut_testpmd.execute_cmd('ptype mapping reset 0')
        self.ptype_mapping_test()
        

    def test_ptype_mapping_replace(self):
        """
        Replace a specific or a group of software defined ptypes with a new one.
        """
        self.ptype_mapping_test()
        self.dut_testpmd.execute_cmd(
            'ptype mapping replace 0 0x06426091 0 0x06421091')
        self.dut_testpmd.execute_cmd('ptype mapping update 0 38 0x06421091')
        check_types = ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN", "TUNNEL_IP", 
                       "INNER_L2_ETHER_VLAN", "INNER_L3_IPV4_EXT_UNKNOWN", 
                       "INNER_L4_NONFRAG"]

        chk_types = { 
            "MAC_IP_IPv6_UDP_PKT":          check_types,
            "MAC_IP_NVGRE_MAC_VLAN_IP_PKT": check_types
        }
        self.ptype_mapping_test(check_ptype = chk_types)
        self.dut_testpmd.execute_cmd(
            'ptype mapping replace 0 0x06421091 1 0x02601091')
        check_types = ["L2_ETHER", "L3_IPV4_EXT_UNKNOWN", "TUNNEL_IP",
                       "INNER_L3_IPV6_EXT_UNKNOWN", "INNER_L4_UDP"]

        chk_types = { 
            "MAC_IP_IPv6_UDP_PKT":          check_types,
            "MAC_IP_NVGRE_MAC_VLAN_IP_PKT": check_types
        }
        self.ptype_mapping_test(check_ptype = chk_types)
        self.dut_testpmd.execute_cmd('ptype mapping reset 0')
        self.ptype_mapping_test()
    
 
    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut_testpmd.quit()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("sed -i '/printf(\" - pktype: 0x%x\", " +\
            "mb->packet_type);/d' app/test-pmd/rxonly.c", "# ", 30)
        self.dut.build_install_dpdk(self.dut.target)
        self.dut.kill_all()
        pass
