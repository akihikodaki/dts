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

import re
import time
from packet import Packet
from pmd_output import PmdOutput
from test_case import TestCase
import rte_flow_common as rfc

vf0_mac = "00:11:22:33:44:55"

tv_MAC_IPV4_L2TPv3_chksum = {'good_checksum': "Ether(dst='%s')/IP(src='192.168.0.3', proto=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('X'*480)" % vf0_mac,
                            'bad_checksum': "Ether(dst='%s')/IP(src='192.168.0.3', proto=115, chksum=0x1234)/L2TP('\\x00\\x00\\x00\\x11')/Raw('X'*480)" % vf0_mac}
tv_MAC_IPV4_ESP_chksum = {'good_checksum': 'Ether(dst="%s")/IP(src="192.168.0.3", proto=50)/ESP(spi=11)/Raw("X"*480)' % vf0_mac,
                        'bad_checksum': 'Ether(dst="%s")/IP(src="192.168.0.3", proto=50, chksum=0x1234)/ESP(spi=11)/Raw("X"*480)' % vf0_mac}
tv_MAC_IPV4_AH_chksum = {'good_checksum': 'Ether(dst="%s")/IP(src="192.168.0.3", proto=50)/AH(spi=11)/Raw("X"*480)' % vf0_mac,
                        'bad_checksum': 'Ether(dst="%s")/IP(src="192.168.0.3", proto=50, chksum=0x1234)/AH(spi=11)/Raw("X"*480)' % vf0_mac}
tv_MAC_IPV4_NAT_T_ESP_chksum = {'good_ip_udp_checksum': 'Ether(dst="%s")/IP(src="192.168.0.20")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)' % vf0_mac,
                        'bad_ip_good_udp_checksum': 'Ether(dst="%s")/IP(src="192.168.0.20", chksum=0x1234)/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)' % vf0_mac,
                       'bad_ip_udp_checksum': 'Ether(dst="%s")/IP(src="192.168.0.20", chksum=0x1234)/UDP(dport=4500,chksum=0x1234)/ESP(spi=2)/Raw("x"*480)' % vf0_mac,
                       'bad_udp_good_ip_checksum':'Ether(dst="%s")/IP(src="192.168.0.20")/UDP(dport=4500,chksum=0x1234)/ESP(spi=2)/Raw("x"*480)' % vf0_mac}
tv_MAC_IPV6_NAT_T_ESP_chksum = {'good_udp_checksum': 'Ether(dst="%s")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500)/ESP(spi=2)/Raw("x"*480)' % vf0_mac,
                       'bad_udp_checksum': 'Ether(dst="%s")/IPv6(src="1111:2222:3333:4444:5555:6666:7777:8888")/UDP(dport=4500,chksum=0x1234)/ESP(spi=2)/Raw("x"*480)' % vf0_mac}

tv_MAC_IPV4_L2TPv3_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IP(proto=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IP(proto=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IP(proto=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV6_L2TPv3_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IPv6(nh=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IPv6(nh=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IPv6(nh=115)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV4_ESP_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IP(proto=50)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IP(proto=50)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IP(proto=50)/ESP(spi=1)/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV6_ESP_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IPv6(nh=50)/ESP(spi=1)/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV4_AH_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IP(proto=51)/AH(spi=1)/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IP(proto=51)/AH(spi=1)/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IP(proto=51)/AH(spi=1)/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV6_AH_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IPv6(nh=51)/AH(spi=1)/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV4_NAT_T_ESP_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)" % vf0_mac}
tv_MAC_IPV6_NAT_T_ESP_vlan = {'matched vlan': "Ether(dst='%s')/Dot1Q(vlan=1)/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'dismatched vlan': "Ether(dst='%s')/Dot1Q(vlan=2)/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)" % vf0_mac,
                            'no vlan': "Ether(dst='%s')/IPv6()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)" % vf0_mac}


class L2tpEspCoverage(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.pmd_output = PmdOutput(self.dut)
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.used_dut_port = self.dut_ports[0]
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.tx_iface = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.verify(self.nic in ["columbiaville_25g", "columbiaville_100g"], "%s nic not support ethertype filter" % self.nic)
        self.vf_flag = False
        self.create_iavf()
        self.pkt = Packet()

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.destroy_iavf()

    def create_iavf(self):

        if self.vf_flag is False:
            self.dut.bind_interfaces_linux('ice')
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
            self.vf_flag = True

            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)

                self.vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
                self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# ")
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def create_testpmd_command(self, port_info, rx_checksum=0):
        """
        Create testpmd command for non-pipeline mode
        """
        
        port_pci = port_info['opt_host']
        if rx_checksum==1:
            param_str = " --rxq=16 --txq=16 --port-topology=loop --enable-rx-cksum "
        else:
            param_str = " --rxq=16 --txq=16 --port-topology=loop "
        self.pmd_output.start_testpmd(cores="1S/8C/1T", param=param_str, eal_param="-w %s" % port_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)

    def enable_hw_checksum(self):
        self.dut.send_expect("stop","testpmd> ")
        self.dut.send_expect("port stop all","testpmd> ")
        self.dut.send_expect("csum set ip hw 0","testpmd> ")
        self.dut.send_expect("csum set udp hw 0","testpmd> ")
        self.dut.send_expect("port start all","testpmd> ")
        self.dut.send_expect("set fwd csum","testpmd> ")
        self.dut.send_expect("set verbose 1","testpmd> ")
        self.dut.send_expect("start","testpmd> ")
    
    def enable_sw_checksum(self):
        self.dut.send_expect("stop","testpmd> ")
        self.dut.send_expect("port stop all","testpmd> ")
        self.dut.send_expect("csum set ip sw 0","testpmd> ")
        self.dut.send_expect("csum set udp sw 0","testpmd> ")
        self.dut.send_expect("port start all","testpmd> ")
        self.dut.send_expect("set fwd csum","testpmd> ")
        self.dut.send_expect("set verbose 1","testpmd> ")
        self.dut.send_expect("start","testpmd> ")
    
    def checksum_verify(self, packets_sent):
        # Send packet.
        self.tester.scapy_foreground()

        for packet_type in list(packets_sent.keys()):
            self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent[packet_type], self.tx_iface))
            self.tester.scapy_execute()
            time.sleep(1)
            out = self.pmd_output.execute_cmd("stop")
            bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
            bad_l4csum = self.pmd_output.get_pmd_value("Bad-l4csum:", out)
            
            if packet_type == 'good_checksum':
                # verify good ip checksum
                self.verify(bad_ipcsum == 0, "good ip csum check error")
            elif packet_type == 'bad_checksum':
                # verify bad ip checksum
                self.verify(bad_ipcsum == 1, "bad ip csum check error")
            elif packet_type == 'bad_udp_checksum':
                # verify bad udp checksum
                self.verify(bad_l4csum == 1, "bad udp csum check error")
            elif packet_type == 'good_udp_checksum':
                # verify good udp checksum
                self.verify(bad_l4csum == 0, "good udp csum check error")
            elif packet_type == 'good_ip_udp_checksum':
                # verify good ip + udp checksum
                self.verify(bad_ipcsum == 0, "good ip csum check error")
                self.verify(bad_l4csum == 0, "good udp csum check error")
            elif packet_type == 'bad_ip_udp_checksum':
                # verify bad ip + udp checksum
                self.verify(bad_ipcsum == 1, "bad ip csum check error")
                self.verify(bad_l4csum == 1, "bad udp csum check error")
            elif packet_type == 'bad_ip_good_udp_checksum':
                # verify bad ip + good udp checksum
                self.verify(bad_ipcsum == 1, "bad ip csum check error")
                self.verify(bad_l4csum == 0, "good udp csum check error")
            else:
                # verify good ip + bad udp checksum
                self.verify(bad_ipcsum == 0, "good ip csum check error")
                self.verify(bad_l4csum == 1, "bad udp csum check error")

            self.pmd_output.execute_cmd("start")
        
    def test_MAC_IPV4_L2TPv3_HW_checksum(self):
        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        self.enable_hw_checksum()
        self.checksum_verify(tv_MAC_IPV4_L2TPv3_chksum)
    
    def test_MAC_IPV4_ESP_HW_checksum(self):
        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        self.enable_hw_checksum()
        self.checksum_verify(tv_MAC_IPV4_ESP_chksum)
    
    def test_MAC_IPV4_AH_HW_checksum(self):
        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        self.enable_hw_checksum()
        self.checksum_verify(tv_MAC_IPV4_AH_chksum)
    
    def test_MAC_IPV4_NAT_T_ESP_HW_checksum(self):
        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        self.enable_hw_checksum()
        self.checksum_verify(tv_MAC_IPV4_NAT_T_ESP_chksum)
    
    def test_MAC_IPV6_NAT_T_ESP_HW_checksum(self):
        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        self.enable_hw_checksum()
        self.checksum_verify(tv_MAC_IPV6_NAT_T_ESP_chksum)
    
    
    def start_tcpdump(self, rxItf):
        self.tester.send_expect("rm -rf getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -A -nn -e -vv -w getPackageByTcpdump.cap -i %s 2> /dev/null& " % rxItf, "#")
        time.sleep(2)

    def get_tcpdump_package(self):
        time.sleep(1)
        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect("tcpdump -A -nn -e -vv -r getPackageByTcpdump.cap", "#")
    
    def vlan_strip_insertion_verify(self,packets_sent):

        # disabel vlan strip, tester will receive the pkt with vlan id
        self.dut.send_expect("vlan set filter on 0","testpmd> ")
        self.dut.send_expect("vlan set strip off 0","testpmd> ")
        self.dut.send_expect("rx_vlan add 1 0","testpmd> ")
        self.dut.send_expect("set fwd mac","testpmd> ")
        self.dut.send_expect("set verbose 1","testpmd> ")
        self.dut.send_expect("start","testpmd> ")
        self.start_tcpdump(self.tx_iface)
        self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent['matched vlan'], self.tx_iface))
        self.tester.scapy_execute()
        time.sleep(1)
        out = self.pmd_output.execute_cmd("stop")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 2, 'vlan id strip off failed')
        self.dut.send_expect("start","testpmd> ")
        self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent['dismatched vlan'], self.tx_iface))
        self.tester.scapy_execute()
        time.sleep(1)
        out = self.pmd_output.execute_cmd("stop")
        pkts= rfc.get_port_rx_packets_number(out,0)
        self.verify(pkts==0, "vlan id filter failed")

        # enable vlan strip, tester will receive the pkt without vlan id
        self.dut.send_expect("vlan set strip on 0","testpmd> ")
        self.start_tcpdump(self.tx_iface)
        self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent['matched vlan'], self.tx_iface))
        self.tester.scapy_execute()
        time.sleep(1)
        out = self.pmd_output.execute_cmd("stop")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')

        # vlan insertion
        self.dut.send_expect("vlan set strip off 0","testpmd> ")
        self.dut.send_expect("port stop all","testpmd> ")
        self.dut.send_expect("tx_vlan set 0 1","testpmd> ")
        self.dut.send_expect("vlan set filter on 0","testpmd> ")
        self.dut.send_expect("rx_vlan add 1 0","testpmd> ")
        self.dut.send_expect("port start all","testpmd> ")
        self.dut.send_expect("start","testpmd> ")
        self.start_tcpdump(self.tx_iface)
        self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent['no vlan'], self.tx_iface))
        self.tester.scapy_execute()
        time.sleep(1)
        out = self.pmd_output.execute_cmd("stop")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan insertion failed')
    
    def test_MAC_IPV4_L2TPv3_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV4_L2TPv3_vlan)
    
    def test_MAC_IPV6_L2TPv3_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV6_L2TPv3_vlan)
    
    def test_MAC_IPV4_ESP_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV4_ESP_vlan)
    
    def test_MAC_IPV6_ESP_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV6_ESP_vlan)
    
    def test_MAC_IPV4_AH_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV4_AH_vlan)

    def test_MAC_IPV6_AH_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV6_AH_vlan)
    
    def test_MAC_IPV4_NAT_T_ESP_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV4_NAT_T_ESP_vlan)
    
    def test_MAC_IPV6_NAT_T_ESP_l2_tag(self):
        self.create_testpmd_command(self.vf0_prop)
        self.vlan_strip_insertion_verify(tv_MAC_IPV6_NAT_T_ESP_vlan)

    def send_pkts_getouput(self, pkts, pf_id=0):
        """
        if pkt_info is True, we need to get packet infomation to check the RSS hash and FDIR.
        if pkt_info is False, we just need to get the packet number and queue number.
        """
        self.send_packets(pkts, pf_id)
        time.sleep(1)
        out_info = self.dut.get_session_output(timeout=1)
        out_pkt = self.pmd_output.execute_cmd("stop")
        out = out_info + out_pkt
        self.pmd_output.execute_cmd("start")
        return out

    def send_packets(self, packets, pf_id=0):
        self.pkt.update_pkt(packets)
        tx_port = self.tx_iface
        self.pkt.send_pkt(crb=self.tester, tx_port=tx_port)

    def test_MAC_IPV4_L2TPv3_HW_checksum_vlan_strip(self):

        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        # vlan strip on
        self.dut.send_expect("vlan set filter on 0","testpmd> ")
        self.dut.send_expect("vlan set strip on 0","testpmd> ")
        self.dut.send_expect("rx_vlan add 1 0","testpmd> ")

        self.enable_hw_checksum()
        #create rule
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1 / end actions queue index 1 / mark id 4 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 2 / end actions queue index 2 / mark id 3 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 3 / end actions queue index 3 / mark id 2 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 4 / end actions queue index 4 / mark id 1 / end","testpmd> ")
        # matched vlan id + bad checksum + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/Dot1Q(vlan=1)/IP(proto=115,chksum=0x123)/L2TP('\\x00\\x00\\x00\\x01')/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4})
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
        # check the vlan strip
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')
        # matched vlan id + bad checksum + mismatched session id
        pkts="Ether(dst='00:11:22:33:44:55')/Dot1Q(vlan=1)/IP(proto=115,chksum=0x123)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
        # check the vlan strip
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')

        # destroy rule
        self.dut.send_expect("flow flush 0","testpmd> ")
        # matched vlan id + bad checksum + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/Dot1Q(vlan=1)/IP(proto=115,chksum=0x123)/L2TP('\\x00\\x00\\x00\\x01')/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
        # check the vlan strip
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')

    def test_MAC_IPV4_L2TPv3_SW_checksum_vlan_insertion(self):

        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        # vlan insertion on
        self.dut.send_expect("vlan set strip off 0","testpmd> ")
        self.dut.send_expect("port stop all","testpmd> ")
        self.dut.send_expect("tx_vlan set 0 1","testpmd> ")
        self.dut.send_expect("vlan set filter on 0","testpmd> ")
        self.dut.send_expect("rx_vlan add 1 0","testpmd> ")
        self.dut.send_expect("port start all","testpmd> ")
        self.dut.send_expect("set fwd mac","testpmd> ")
        self.dut.send_expect("set verbose 1","testpmd> ")
        self.dut.send_expect("start","testpmd> ")

        #create rule
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 1 / end actions queue index 1 / mark id 4 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 2 / end actions queue index 2 / mark id 3 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 3 / end actions queue index 3 / mark id 2 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / l2tpv3oip session_id is 4 / end actions queue index 4 / mark id 1 / end","testpmd> ")
        # no vlan + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/IP(proto=115)/L2TP('\\x00\\x00\\x00\\x01')/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        time.sleep(1)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4})
        # check the vlan insertion
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan insertion failed')
        
        self.enable_sw_checksum()
        # bad checksum + mismatched session id
        pkts="Ether(dst='00:11:22:33:44:55')/IP(proto=115,chksum=0x123)/L2TP('\\x00\\x00\\x00\\x11')/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")

        # destroy rule
        self.dut.send_expect("flow flush 0","testpmd> ")
        # bad checksum + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/IP(proto=115,chksum=0x123)/L2TP('\\x00\\x00\\x00\\x01')/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
    

    def test_MAC_IPV4_ESP_HW_checksum_vlan_strip(self):

        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        # vlan strip on
        self.dut.send_expect("vlan set filter on 0","testpmd> ")
        self.dut.send_expect("vlan set strip on 0","testpmd> ")
        self.dut.send_expect("rx_vlan add 1 0","testpmd> ")

        self.enable_hw_checksum()
        #create rule
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / esp spi is 1 / end actions queue index 1 / mark id 4 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / esp spi is 2 / end actions queue index 2 / mark id 3 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / esp spi is 3 / end actions queue index 3 / mark id 2 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / esp spi is 4 / end actions queue index 4 / mark id 1 / end","testpmd> ")
        # matched vlan id + bad checksum + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/Dot1Q(vlan=1)/IP(proto=50,chksum=0x123)/ESP(spi=1)/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4})
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
        # check the vlan strip
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')
        # matched vlan id + bad checksum + mismatched session id
        pkts="Ether(dst='00:11:22:33:44:55')/Dot1Q(vlan=1)/IP(proto=50,chksum=0x123)/ESP(spi=11)/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
        # check the vlan strip
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')

        # destroy rule
        self.dut.send_expect("flow flush 0","testpmd> ")
        # matched vlan id + bad checksum + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/Dot1Q(vlan=1)/IP(proto=50,chksum=0x123)/ESP(spi=1)/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")
        # check the vlan strip
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan id strip on failed')

    def test_MAC_IPV4_NAT_T_ESP_SW_checksum_vlan_insertion(self):

        self.create_testpmd_command(self.vf0_prop,rx_checksum=1)
        # vlan insertion on
        self.dut.send_expect("vlan set strip off 0","testpmd> ")
        self.dut.send_expect("port stop all","testpmd> ")
        self.dut.send_expect("tx_vlan set 0 1","testpmd> ")
        self.dut.send_expect("vlan set filter on 0","testpmd> ")
        self.dut.send_expect("rx_vlan add 1 0","testpmd> ")
        self.dut.send_expect("port start all","testpmd> ")
        self.dut.send_expect("set fwd mac","testpmd> ")
        self.dut.send_expect("set verbose 1","testpmd> ")
        self.dut.send_expect("start","testpmd> ")

        #create rule
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 1 / end actions queue index 1 / mark id 4 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 2 / end actions queue index 2 / mark id 3 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 3 / end actions queue index 3 / mark id 2 / end","testpmd> ")
        self.dut.send_expect("flow create 0 ingress pattern eth / ipv4 / udp / esp spi is 4 / end actions queue index 4 / mark id 1 / end","testpmd> ")
        # no vlan +  matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/IP()/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4})
        # check the vlan insertion
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'vlan insertion failed')
        
        self.enable_sw_checksum()
        # bad checksum + mismatched session id
        pkts="Ether(dst='00:11:22:33:44:55')/IP(chksum=0x123)/UDP(dport=4500)/ESP(spi=11)/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")

        # destroy rule
        self.dut.send_expect("flow flush 0","testpmd> ")
        # bad checksum + matched session id
        pkts="Ether(dst='00:11:22:33:44:55')/IP(chksum=0x123)/UDP(dport=4500)/ESP(spi=1)/Raw('x'*480)"
        self.start_tcpdump(self.tx_iface)
        out = self.send_pkts_getouput(pkts)
        # check the fdir rule
        rfc.check_iavf_fdir_mark(out, pkt_num=1, check_param={"port_id": 0, "queue": 1, "mark_id": 4},stats=False)
        # check the rx checksum 
        bad_ipcsum = self.pmd_output.get_pmd_value("Bad-ipcsum:", out)
        self.verify(bad_ipcsum == 1, "bad ip csum check error")  




