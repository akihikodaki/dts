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

import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestQinqFilter(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        """
        global dutRxPortId
        global dutTxPortId

        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortville_25g", 'foxville', 'carlsville'],
                    "NIC %s not support this test" % self.nic)
        print('this case only supports fortville with 6.0.0+ firmware and dpdk17.05+')
        ports = self.dut.get_ports()
        # Verify that enough ports are available
        self.verify(len(ports) >= 1, "Insufficient ports")

        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        dutRxPortId = valports[0]
        dutTxPortId = valports[0]

        port = self.tester.get_local_port(dutRxPortId)
        self.txItf = self.tester.get_interface(port)
        self.smac = self.tester.get_mac(port)
        # the packet dest mac must is dut tx port id when the port promisc is off
        self.dmac = self.dut.get_mac_address(dutRxPortId)

        self.portMask = utils.create_mask(valports[:1])
        
        cores = self.dut.get_core_list('1S/2C/1T')
        self.coreMask = utils.create_mask(cores)
        self.path=self.dut.apps_name['test-pmd']
        
    def vlan_send_packet(self, vlans):
        """
        Send $num of packet to portid, vlans must a list. the member is (vlan id,vlan values).
        eg: vlans = [(0x8100, 1),(0x8100, 4093)]
        """

        vlanString = 'sendp([Ether( dst="%s", src="%s")/' % (self.dmac, self.smac)
        for vlan_config in vlans:
            vlanString += "Dot1Q(id=%s,vlan=%s)/" % vlan_config
        vlanString += 'IP(src="192.168.0.1", dst="192.168.0.2")/Raw("x" * 20)],iface="%s")' % self.txItf

        self.tester.scapy_append(vlanString)
        self.tester.scapy_execute()

    def creat_pcap(self, vlans_list):
        """
        create pcap and changed out vlan tpid to 0x88a8
        """
        packets = []
        for vlan in vlans_list:
            packets.append(Ether(dst=self.dmac, src=self.smac)/Dot1Q(id=0x8100,vlan=vlan[0])/Dot1Q(id=0x8100,vlan=vlan[1])/IP(src="192.168.0.1", dst="192.168.0.2")/Raw("x"*20))
        self.tester.send_expect('rm -rf tmp_qinq.pcap', "# ")
        self.tester.send_expect('rm -rf dst_qinq.pcap', "# ")
        wrpcap('tmp_qinq.pcap', packets)
        
        fr = open('tmp_qinq.pcap', 'rb')
        packet_bin = []
        while 1:
            s = fr.read(1)
            if not s:
                break
            packet_bin.append(s)
        match_bin = (['\x81', '\x00', '\x00', '\x01'],
                     ['\x81', '\x00', '\x00', '\x02'],
                     ['\x81', '\x00', '\x00', '\x03'])
        for i in range(len(packet_bin) - len(match_bin[0])):
            if packet_bin[i: i+ len(match_bin[0])] in match_bin:
                packet_bin[i:i + len(match_bin[0]) - 1] = ['\x88','\xa8', '\x00']
        fw = open('/root/dst_qinq.pcap', 'wb')
        for word in packet_bin:
            fw.write(word)
        fw.close()

    def config_vfs(self, port_id, vfs):
        """
        if vfs is 0, call destroy_sriov_vfs_by_port in dut for destory vf.
        if vfs > 0, call generate_sriov_vfs_by_port generate vf and bind igb_uio to vf
        """
        if vfs:
            self.dut.generate_sriov_vfs_by_port(port_id, vfs, 'igb_uio')
            for port in self.dut.ports_info[port_id]['vfs_port']:
                port.bind_driver('igb_uio')
        else:
            self.dut.destroy_sriov_vfs_by_port(port_id)
        
        
    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_qinq_pack_type(self):
        """
        Enable receipt of dual VLAN packets
        """
        self.logger.info('\r\n-------------------------this case only support novector mode to start testpmd!-------------------------\r\n')
        pmd_out = PmdOutput(self.dut)
        pmd_out.start_testpmd("1S/2C/1T", eal_param="--force-max-simd-bitwidth=64", param="--portmask=%s --port-topology=loop --rxq=4 --txq=4 --disable-rss" % self.portMask)
        self.dut.send_expect("vlan set extend on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("vlan set strip on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("vlan set qinq_strip on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(5)
      
        self.vlan_send_packet([(0x8100, 2), (0x8100, 3)])
        out = self.dut.get_session_output()
        self.verify('QinQ VLAN' in out, "dual vlan not received:" + str(out))

        self.dut.send_expect("quit", "#")

    def test_qinq_filter_PF_queues(self):
        """
        qinq filter packet received by assign PF queues
        """
        eal_para = self.dut.create_eal_parameters(cores='1S/2C/1T')
        self.dut.send_expect(r'%s %s -- -i \
                               --portmask=%s --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' % (self.path, eal_para, self.portMask),
                               "testpmd> ", 30)
        self.dut.send_expect("vlan set extend on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(5)
        
        # out vlan 1, inner vlan 4093 packet will received by PF queue 1
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 1 / vlan tci is 4093 / end actions pf / queue index 1 / end', "testpmd> ")
                               
        # out vlan 2, inner vlan 4094 packet will received by PF queue 1
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 4094 / end actions pf / queue index 2 / end', "testpmd> ")
                               
        self.vlan_send_packet([(0x8100, 1), (0x8100, 4093)])
        out = self.dut.get_session_output()
        self.verify('queue 1: received 1 packets' in out, "out vlan 1, inner vlan 4093 received not by queue 1 : %s" % out)
        
        self.vlan_send_packet([(0x8100, 2), (0x8100, 4094)])
        out = self.dut.get_session_output()
        self.verify('queue 2: received 1 packets' in out, "out vlan 1, inner vlan 4093 received not by queue 2 : %s" % out)
        
        self.dut.send_expect("quit", "#")
        
    def test_qinq_packet_filter_VF_queues(self):
        """
        qinq filter packet received by assign VF queues
        """
        self.config_vfs(dutRxPortId, 2)
        vf_list = self.dut.ports_info[dutRxPortId]['sriov_vfs_pci']
        self.verify(len(vf_list) == 2, 'config 2 vf failed: %s' % str(vf_list))
        vf0_session = self.dut.new_session('qinq_filter')
        vf1_session = self.dut.new_session('qinq_filter')

        eal_para = self.dut.create_eal_parameters(cores='1S/2C/1T', prefix='pf', ports=[self.dut.ports_info[dutRxPortId]['pci']])
        self.dut.send_expect(r'%s %s -- -i --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' 
                               % (self.path, eal_para),
                               "testpmd> ", 30)
        self.dut.send_expect("vlan set extend on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)

        # out vlan 1, inner vlan 4093 packet will received by vf0 queue 2
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 1 / vlan tci is 4093 / end actions vf id 0 / queue index 2 / end', "testpmd> ")
        # out vlan 2, inner vlan 4094 packet will received by vf1 queue 3
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 4094 / end actions vf id 1 / queue index 3 / end', "testpmd> ")
        # out vlan 3, inner vlan 4094 packet will received by pf queue 1
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 3 / vlan tci is 4094 / end actions pf / queue index 1 / end', "testpmd> ")

        vf0_session.send_expect(r'%s -c %s -n 4  \
                               --socket-mem=1024,1024 --file-prefix=vf0 -a %s -- -i --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' 
                               % (self.path, self.coreMask, vf_list[0]),
                               "testpmd> ", 30)
                                                              
        vf1_session.send_expect(r'%s -c %s -n 4 \
                               --socket-mem=1024,1024 --file-prefix=vf1 -a %s -- -i --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' 
                               % (self.path, self.coreMask, vf_list[1]),
                               "testpmd>", 30)
        for session_name in [vf0_session, vf1_session]:
            session_name.send_expect("set fwd rxonly", "testpmd> ")
            session_name.send_expect("set verbose 1", "testpmd> ")
            session_name.send_expect("start", "testpmd> ", 120)
            time.sleep(5)
        for vlan_config in [[(0x8100, 1),(0x8100, 4093)], [(0x8100, 2),(0x8100, 4094)], [(0x8100, 3),(0x8100, 4094)]]:
            self.vlan_send_packet(vlan_config)
    
        dut_out = self.dut.get_session_output()
        vf0_out = vf0_session.get_session_before(30)
        vf1_out = vf1_session.get_session_before(30)
         
        error_message = ''
        if 'queue 1: received 1 packets' not in dut_out:
            error_message += 'dut testpmd received packt queue error: %s' % dut_out
        elif 'queue 2: received 1 packets' not in vf0_out:
            error_message += ' vf0 testpmd received packt queue error: %s' % vf0_out
        elif 'queue 3: received 1 packets' not in vf1_out:
            error_message += ' vf1 testpmd received packt queue error: %s' % vf1_out
             
        for session_name in [vf0_session, vf1_session]:
            session_name.send_expect("quit", "#")
            self.dut.close_session(session_name)
        self.dut.send_expect("quit", "#")
         
        self.config_vfs(dutRxPortId, 0)
        vf_list = self.dut.ports_info[dutRxPortId]['sriov_vfs_pci']
        self.verify(len(vf_list) == 0, 'destroy vf failed: %s' % str(vf_list))
        
        self.verify(not error_message, error_message)
        
    def test_qinq_filter_with_diffierent_tpid(self):
        """
        qinq filter packet with different tpid  received by assign VF queues
        """
        self.config_vfs(dutRxPortId, 2)
        vf_list = self.dut.ports_info[dutRxPortId]['sriov_vfs_pci']
        self.verify(len(vf_list) == 2, 'config 2 vf failed: %s' % str(vf_list))
        vf0_session = self.dut.new_session('qinq_filter')
        vf1_session = self.dut.new_session('qinq_filter')

        eal_para = self.dut.create_eal_parameters(cores='1S/2C/1T', prefix='pf', ports=[self.dut.ports_info[dutRxPortId]['pci']])
        self.dut.send_expect(r'%s %s -- -i --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' 
                               % (self.path, eal_para),
                               "testpmd> ", 30)
        self.dut.send_expect("vlan set extend on %s" % dutRxPortId, "testpmd> ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(5)

        # out vlan 1, inner vlan 4093 packet will received by vf0 queue 2
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 1 / vlan tci is 4093 / end actions vf id 0 / queue index 2 / end', "testpmd> ")
        # out vlan 2, inner vlan 4094 packet will received by vf1 queue 3
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 2 / vlan tci is 4094 / end actions vf id 1 / queue index 3 / end', "testpmd> ")
        # out vlan 3, inner vlan 4094 packet will received by pf queue 1
        self.dut.send_expect(r'flow create 0 ingress pattern eth / vlan tci is 3 / vlan tci is 4094 / end actions pf / queue index 1 / end', "testpmd> ")
                               
        self.dut.send_expect('vlan set outer tpid 0x88a8 0', "testpmd")
        
        vf0_session.send_expect(r'%s -c %s -n 4 \
                               --socket-mem=1024,1024 --file-prefix=vf0 -a %s -- -i --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' 
                               % (self.path, self.coreMask, vf_list[0]),
                               "testpmd> ", 30)
                                                              
        vf1_session.send_expect(r'%s -c %s -n 4 \
                               --socket-mem=1024,1024 --file-prefix=vf1 -a %s -- -i --port-topology=loop \
                               --rxq=4 --txq=4  --disable-rss' 
                               % (self.path, self.coreMask, vf_list[1]),
                               "testpmd>", 30)
        for session_name in [vf0_session, vf1_session]:
            session_name.send_expect("set fwd rxonly", "testpmd> ")
            session_name.send_expect("set verbose 1", "testpmd> ")
            session_name.send_expect("start", "testpmd> ", 120)
            time.sleep(5)
        
        self.creat_pcap([(1, 4093), (2, 4094), (3, 4094)])
        
        self.tester.scapy_append('pcap = rdpcap("/root/dst_qinq.pcap")')
        self.tester.scapy_append('sendp(pcap, iface="%s")' % self.txItf)
        self.tester.scapy_execute()
        time.sleep(5)
      
        dut_out = self.dut.get_session_output()
        vf0_out = vf0_session.get_session_before(30)
        vf1_out = vf1_session.get_session_before(30)
         
        error_message = ''
        if 'queue 1: received 1 packets' not in dut_out:
            error_message += 'dut testpmd received packt queue error: %s' % dut_out
        elif 'queue 2: received 1 packets' not in vf0_out:
            error_message += ' vf0 testpmd received packt queue error: %s' % vf0_out
        elif 'queue 3: received 1 packets' not in vf1_out:
            error_message += ' vf1 testpmd received packt queue error: %s' % vf1_out
             
        for session_name in [vf0_session, vf1_session]:
            session_name.send_expect("quit", "#")
            self.dut.close_session(session_name)
        self.dut.send_expect("quit", "#")
         
        self.config_vfs(dutRxPortId, 0)
        vf_list = self.dut.ports_info[dutRxPortId]['sriov_vfs_pci']
        self.verify(len(vf_list) == 0, 'destroy vf failed: %s' % str(vf_list))
        
        self.verify(not error_message, error_message)
    

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
