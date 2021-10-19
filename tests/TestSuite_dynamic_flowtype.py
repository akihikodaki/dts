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

import framework.packet as packet
import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

VM_CORES_MASK = 'all'


class TestDynamicFlowtype(TestCase):

    def set_up_all(self):
        self.verify('fortville' in self.nic,
                    'dynamic flow type mapping can not support %s nic'
                    % self.nic)
        ports = self.dut.get_ports()
        self.verify(len(ports) >= 1, "Insufficient ports for testing")
        valports = [_ for _ in ports if self.tester.get_local_port(_) != -1]
        self.dut_port = valports[0]
        tester_port = self.tester.get_local_port(self.dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        profile_file = 'dep/gtp.pkgo'
        profile_dst = "/tmp/"
        self.dut.session.copy_file_to(profile_file, profile_dst)
        PF_Q_strip = 'RTE_LIBRTE_I40E_QUEUE_NUM_PER_PF'
        self.PF_QUEUE = self.search_queue_number(PF_Q_strip)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_testpmd.start_testpmd(
            "Default", "--port-topology=chained --txq=%s --rxq=%s"
            % (self.PF_QUEUE, self.PF_QUEUE))
        self.load_profile()

    def search_queue_number(self, Q_strip):
        """
        Search max queue number from configuration.
        """
        out = self.dut.send_expect("cat config/rte_config.h", "]# ", 10)
        pattern = "define (%s) (\d*)" % Q_strip
        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print((utils.RED('Search no queue number.')))
            return None
        else:
            queue = res.group(2)
            return int(queue)

    def load_profile(self):
        """
        Load profile to update FVL configuration tables, profile will be
        stored in binary file and need to be passed to AQ to program FVL
        during initialization stage.
        """
        self.dut_testpmd.execute_cmd('port stop all')
        time.sleep(1)
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.dut_testpmd.execute_cmd('ddp add 0 /tmp/gtp.pkgo,/tmp/gtp.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("Profile number is: 1" in out,
                    "Failed to load ddp profile!!!")
        self.dut_testpmd.execute_cmd('port start all')
        time.sleep(1)
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')

    def gtp_packets(self, flowtype=26, match_opt='matched'):
        """
        Generate different GTP types according to different parameters.
        I40e PCTYPEs are statically mapped to RTE_ETH_FLOW_* types in
        DPDK, defined in rte_eth_ctrl.h, and flow types used to define
        ETH_RSS_* offload types in rte_ethdev.h. RTE_ETH_FLOW_MAX is
        defined now as 22, leaves 42 flow type unassigned.
        Input:
        flowtype: define flow type 26, 23, 24, 25 for GTP types as below
                  table, check each layer type, tunnel packet includes
                  GTPC and GTPU, GTPC has none inner L3, GTPU has none,
                  IPV4 and IPV6 inner L3.
        match_opt: PF or VSIs receive match packets to rss queue, but
                   receive not match packets to queue 0.

        +------------+------------+------------+
        |Packet Type |   PCTYPEs  | Flow Types |
        +------------+------------+------------+
        |GTP-U IPv4  |    22      |   26       |
        +------------+------ -----+------------+
        |GTP-U IPv6  |    23      |   23       |
        +------------+------------+------------+
        |GTP-U PAY4  |    24      |   24       |
        +------------+------------+------------+
        |GTP-C PAY4  |    25      |   25       |
        +------------+------------+------------+

        """
        pkts = []
        pkts_ipv4 = {'IPV4': 'Ether()/IP()/Raw("X"*20)'}

        pkts_gtpc_pay = {'IPV4/GTPC': 'Ether()/IP()/UDP(dport=2123)/GTP_U_Header()/Raw("X"*20)',
                         'IPV6/GTPC': 'Ether()/IPv6()/UDP(dport=2123)/GTP_U_Header()/Raw("X"*20)'}

        pkts_gtpu_pay = {'IPV4/GTPU': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/Raw("X"*20)',
                         'IPV6/GTPU': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/Raw("X"*20)'}

        pkts_gtpu_ipv4 = {'IPV4/GTPU/IPV4': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV4/FRAG': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP(frag=5)/Raw("X"*20)',
                          'IPV4/GTPU/IPV4/UDP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/UDP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV4/TCP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/TCP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV4/SCTP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/SCTP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV4/ICMP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IP()/ICMP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV4': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV4/FRAG': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP(frag=5)/Raw("X"*20)',
                          'IPV6/GTPU/IPV4/UDP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/UDP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV4/TCP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/TCP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV4/SCTP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/SCTP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV4/ICMP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IP()/ICMP()/Raw("X"*20)'}

        pkts_gtpu_ipv6 = {'IPV4/GTPU/IPV6/FRAG': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/IPv6ExtHdrFragment()/Raw("X"*20)',
                          'IPV4/GTPU/IPV6': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/Raw("X"*20)',
                          'IPV4/GTPU/IPV6/UDP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV6/TCP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/TCP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV6/SCTP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6()/SCTP()/Raw("X"*20)',
                          'IPV4/GTPU/IPV6/ICMP': 'Ether()/IP()/UDP(dport=2152)/GTP_U_Header()/IPv6(nh=58)/ICMP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV6/FRAG': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/IPv6ExtHdrFragment()/Raw("X"*20)',
                          'IPV6/GTPU/IPV6': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/Raw("X"*20)',
                          'IPV6/GTPU/IPV6/UDP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/UDP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV6/TCP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/TCP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV6/SCTP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6()/SCTP()/Raw("X"*20)',
                          'IPV6/GTPU/IPV6/ICMP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header()/IPv6(nh=58)/ICMP()/Raw("X"*20)'}

        if match_opt == 'matched':
            # Define flow type for IPV4 as 2 in rte_eth_ctrl.h
            if flowtype == 2:
                pkts = pkts_ipv4
            if flowtype == 23:
                pkts = pkts_gtpu_ipv6
            if flowtype == 24:
                pkts = pkts_gtpu_pay
            if flowtype == 25:
                pkts = pkts_gtpc_pay
            if flowtype == 26:
                pkts = pkts_gtpu_ipv4

        if match_opt == 'not matched':
            if flowtype == 23:
                pkts = dict(list(pkts_gtpc_pay.items()) +
                            list(pkts_gtpu_pay.items()) +
                            list(pkts_gtpu_ipv4.items()))
            if flowtype == 24:
                pkts = dict(list(pkts_gtpc_pay.items()) +
                            list(pkts_gtpu_ipv4.items()) +
                            list(pkts_gtpu_ipv6.items()))
            if flowtype == 25:
                pkts = dict(list(pkts_gtpu_pay.items()) +
                            list(pkts_gtpu_ipv4.items()) +
                            list(pkts_gtpu_ipv6.items()))
            if flowtype == 26:
                pkts = dict(list(pkts_gtpc_pay.items()) +
                            list(pkts_gtpu_pay.items()) +
                            list(pkts_gtpu_ipv6.items()))

        return pkts

    def packet_send_verify(self, flowtype=26, match_opt='matched'):
        """
        Send packet and verify rss function.
        """
        pkts = self.gtp_packets(flowtype, match_opt)
        for packet_type in list(pkts.keys()):
            pkt = packet.Packet(pkts[packet_type])
            pkt.send_pkt(crb=self.tester, tx_port=self.tester_intf)
            out = self.dut.get_session_output(timeout=2)
            if match_opt == 'matched':
                self.verify("PKT_RX_RSS_HASH" in out,
                            "Failed to receive packet in rss queue!!!")
            elif match_opt == 'not matched':
                self.verify("port 0/queue 0" in out,
                            "Failed to receive packet in queue 0!!!")
                self.verify("PKT_RX_RSS_HASH" not in out,
                            "Failed to receive packet in queue 0!!!")

    def dynamic_flowtype_test(self, pctype=22, flowtype=26, reset=False):
        """
        Dynamic modify, return or reset the contents of flow type to pctype
        dynamic mapping, enable rss hash for new protocol.
        reset: If reset is true, reset the contents of flow type to pctype
               mapping. If reset is false, enable rss hash for new protocal.
        """
        out = self.dut_testpmd.execute_cmd('show port 0 pctype mapping')
        self.verify("pctype: 63  ->  flowtype: 14" in out,
                    "Failed show flow type to pctype mapping!!!")
        self.verify("pctype: %s  ->  flowtype: %s"
                    % (pctype, flowtype) not in out,
                    "Failed show flow type to pctype mapping!!!")
        self.dut_testpmd.execute_cmd(
            'port config 0 pctype mapping update %s %s' % (pctype, flowtype))
        out = self.dut_testpmd.execute_cmd('show port 0 pctype mapping')
        self.verify("pctype: %s  ->  flowtype: %s"
                    % (pctype, flowtype) in out,
                    "Failed update flow type to pctype mapping!!!")
        if reset is False:
            self.dut_testpmd.execute_cmd('port config all rss %s' % flowtype)
        else:
            self.dut_testpmd.execute_cmd('port config 0 pctype mapping reset')
            out = self.dut_testpmd.execute_cmd('show port 0 pctype mapping')
            self.verify("pctype: %s  ->  flowtype: %s"
                        % (pctype, flowtype) not in out,
                        "Failed reset flow type to pctype mapping!!!")
            """
            Send normal ipv4 packet to test rss, rte_eth_ctrl.h defines flow
            type for IPV4 is 2.
            """
            flowtype = 2
        for match_opt in ['matched', 'not matched']:
            if match_opt == 'not matched' and reset is True:
                break
            self.packet_send_verify(flowtype, match_opt)

    def test_profile_correctness(self):
        """
        GTP is supported by NVM with profile updated. Check profile
        information correctness, includes used protocols, packet
        classification types, defined packet types and so on.
        """
        out = self.dut_testpmd.execute_cmd('ddp get info /tmp/gtp.pkgo')
        self.verify("i40e Profile Version" in out,
                    "Failed to verify profile version!!!")
        self.verify("List of used protocols" in out,
                    "Failed to verify profie used protocols!!!")
        self.verify("List of defined packet classification types" in out,
                    "Failed to verify profile packet classification types!!!")
        self.verify("List of defined packet types" in out,
                    "Failed to verify profile packet types!!!")

    def test_dynamic_flowtype_reset(self):
        """
        Dynamic modify, reset and return the contents of flow type to pctype
        dynamic mapping.
        """
        self.dynamic_flowtype_test(pctype=22, flowtype=26, reset=True)

    def test_dynamic_flowtype_gtpu_ipv4(self):
        """
        Dynamic modify, return the contents of flow type to pctype dynamic
        mapping, enable and verify rss for GTP-U IPV4 packets.
        """
        self.dynamic_flowtype_test(pctype=22, flowtype=26, reset=False)

    def test_dynamic_flowtype_gtpu_ipv6(self):
        """
        Dynamic modify, return the contents of flow type to pctype dynamic
        mapping, enable and verify rss for GTP-U IPV6 packets.
        """
        self.dynamic_flowtype_test(pctype=23, flowtype=23, reset=False)

    def test_dynamic_flowtype_gtpu_pay(self):
        """
        Dynamic modify, return the contents of flow type to pctype dynamic
        mapping, enable and verify rss for GTP-U PAY packets.
        """
        self.dynamic_flowtype_test(pctype=24, flowtype=24, reset=False)

    def test_dynamic_flowtype_gtpc_pay(self):
        """
        Dynamic modify, return the contents of flow type to pctype dynamic
        mapping, enable and verify rss for GTP-C PAY packets.
        """
        self.dynamic_flowtype_test(pctype=25, flowtype=25, reset=False)

    def tear_down(self):
        self.dut_testpmd.execute_cmd('stop')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        if "Profile number is: 0" not in out:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd('ddp del 0 /tmp/gtp.bak')
            out = self.dut_testpmd.execute_cmd('ddp get list 0')
            self.verify("Profile number is: 0" in out,
                        "Failed to delete ddp profile!!!")
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.quit()

    def tear_down_all(self):
        self.dut.kill_all()
