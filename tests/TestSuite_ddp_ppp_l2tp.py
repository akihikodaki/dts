# <COPYRIGHT_TAG>

import time
import re
import sys
import utils
from test_case import TestCase
from pmd_output import PmdOutput
from settings import get_nic_name
from scapy.all import *
import random


class TestDdpPppL2tp(TestCase):

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        profile_file = 'dep/ppp-oe-ol2tpv2.pkgo'
        profile_dst = "/tmp/"
        self.dut.session.copy_file_to(profile_file, profile_dst)
        out = self.dut.send_expect("cat config/common_base", "]# ", 10)
        self.PF_Q_strip = 'CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_PF'
        pattern = "(%s=)(\d*)" % self.PF_Q_strip
        self.PF_QUEUE = self.element_strip(out, pattern)
        self.used_dut_port = self.dut_ports[0]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        self.dut_testpmd = PmdOutput(self.dut)

    def set_up(self):
        self.load_profile()

    def element_strip(self, out, pattern):
        """
        Strip and get queue number.
        """
        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print((utils.RED('Search no queue number.')))
            return None
        else:
            result = res.group(2)
            return int(result)

    def load_profile(self):
        """
        Load profile to update FVL configuration tables, profile will be
        stored in binary file and need to be passed to AQ to program FVL
        during initialization stage.
        """
        self.dut_testpmd.start_testpmd(
            "Default", "--pkt-filter-mode=perfect --port-topology=chained \
            --txq=%s --rxq=%s"
            % (self.PF_QUEUE, self.PF_QUEUE))
        self.dut_testpmd.execute_cmd('port stop all')
        time.sleep(1)
        self.dut_testpmd.execute_cmd(
            'ddp add 0 /tmp/ppp-oe-ol2tpv2.pkgo,/tmp/ppp-oe-ol2tpv2.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("Profile number is: 1" in out,
                    "Failed to load ddp profile!!!")
        self.dut_testpmd.execute_cmd('port start all')

    def ppp_l2tp_pkts(self, flowtype, keyword):
        """
        Generate PPPoE, L2TPv2 and PPPoL2TPv2 packets.
        """
        src_mac = "3C:FD:FE:A3:A0:01"
        dst_mac = "4C:FD:FE:A3:A0:01"
        src_ip = "1.1.1.1"
        dst_ip = "2.2.2.2"
        src_ipv6 = "1001:0db8:85a3:0000:0000:8a2e:0370:0001"
        dst_ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:0001"
        session_id = hex(0x7)
        sport = 4000
        dport = 8000
        if keyword is not 'def':
            if keyword is 'src_mac':
                src_mac = "3C:FD:FE:A3:A0:02"
            if keyword is 'dst_mac':
                dst_mac = "4C:FD:FE:A3:A0:02"
            if keyword is 'src_ip':
                src_ip = "1.1.1.2"
            if keyword is 'dst_ip':
                dst_ip = "2.2.2.3"
            if keyword is 'src_ipv6':
                src_ipv6 = "1001:0db8:85a3:0000:0000:8a2e:0370:0002"
            if keyword is 'dst_ipv6':
                dst_ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:0002"
            if keyword is 'session_id':
                session_id = hex(0x8)
            if keyword is 'sport':
                sport = 4001
            if keyword is 'dport':
                dport = 8001
        if flowtype == 23:
            pkts = {'IPV4/L2TP/IPV4/UDP': 'Ether()/IP()/UDP(sport=1701,dport=1701)/PPP_L2TP(proto=0x0021,session_id=%s)/IP(src="%s",dst="%s")/UDP(sport=%d, dport=%d)/Raw("X"* 20)'
                    % (session_id, src_ip, dst_ip, sport, dport)}
        if flowtype == 24:
            pkts = {'IPV4/L2TP/IPV6/UDP': 'Ether()/IP()/UDP(sport=1701, dport=1701)/PPP_L2TP(proto=0x0057,session_id=%s)/IPv6(src="%s", dst="%s")/UDP(sport=%d, dport=%d)/Raw("X"* 20)'
                    % (session_id, src_ipv6, dst_ipv6, sport, dport)}
        if flowtype == 26:
            pkts = {'IPV4/L2TP': 'Ether(src="%s", dst="%s")/IP()/UDP(dport=1701, sport=1701)/L2TP(session_id=%s)/Raw("X"*20)'
                    % (src_mac, dst_mac, session_id)}
        if flowtype == 28:
            pkts = {'PPPOE/IPV4/UDP': 'Ether()/PPPoE(sessionid=%s)/PPP(proto=0x21)/IP(src="%s",dst="%s")/UDP(sport=%d,dport=%d)/Raw("X"*20)'
                    % (session_id, src_ip, dst_ip, sport, dport)}
        if flowtype == 29:
            pkts = {'PPPOE/IPV6/UDP': 'Ether()/PPPoE(sessionid=%s)/PPP(proto=0x57)/IPv6(src="%s",dst="%s")/UDP(sport=%d,dport=%d)/Raw("X"*20)'
                    % (session_id, src_ipv6, dst_ipv6, sport, dport)}
        if flowtype == 30:
            pkts = {'PPPOE': 'Ether(src="%s", dst="%s")/PPPoE(sessionid=%s)'
                    % (src_mac, dst_mac, session_id)}
        return pkts

    def raw_packet_generate(self, flowtype):
        """
        setup raw flow type filter for flow director, source/destination
        fields (both IP addresses and UDP ports) should be swapped in
        template file and packets sent to NIC.
        """
        if flowtype == 23:
            a = Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0021, session_id=0x7)/IP(dst="1.1.1.1", src="2.2.2.2")/UDP(dport=4000, sport=8000)
        if flowtype == 24:
            a = Ether()/IP()/UDP(dport=1701, sport=1701)/PPP_L2TP(proto=0x0057, session_id=0x7)/IPv6(dst="1001:0db8:85a3:0000:0000:8a2e:0370:0001", src="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP(dport=4000, sport=8000)/Raw("X"*20)
        if flowtype == 26:
            a = Ether(dst="3C:FD:FE:A3:A0:01", src="4C:FD:FE:A3:A0:01")/IP()/UDP(dport=1701, sport=1701)/L2TP(session_id=0x7)/Raw("X"*20)
        if flowtype == 28:
            a = Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x21)/IP(dst="1.1.1.1", src="2.2.2.2")/UDP(dport=4000, sport=8000)/Raw("X"*20)
        if flowtype == 29:
            a = Ether()/PPPoE(sessionid=0x7)/PPP(proto=0x57)/IPv6(dst="1001:0db8:85a3:0000:0000:8a2e:0370:0001", src="2001:0db8:85a3:0000:0000:8a2e:0370:0001")/UDP(dport=4000, sport=8000)/Raw("X"*20)
        if flowtype == 30:
            a = Ether(dst="3C:FD:FE:A3:A0:01", src="4C:FD:FE:A3:A0:01")/PPPoE(sessionid=0x7)
        ba = bytearray(bytes(a))
        rawfile_src = '/tmp/test.raw'
        File = open("%s" % rawfile_src, "wb")
        File.write(ba)
        File.close()
        rawfile_dst = "/tmp/"
        self.dut.session.copy_file_to(rawfile_src, rawfile_dst)

    def send_and_verify(self, flowtype, keyword='def', type='rss'):
        """
        Send packets and verify result.
        """
        pkts = self.ppp_l2tp_pkts(flowtype, keyword)
        for packet_type in list(pkts.keys()):
            self.tester.scapy_append(
                'sendp([%s], iface="%s")'
                % (pkts[packet_type], self.tester_intf))
            self.tester.scapy_execute()
            out = self.dut.get_session_output(timeout=2)
            print(out)
            if type is 'rss':
                self.verify("PKT_RX_RSS_HASH" in out, "Failed to test RSS!!!")
            pattern = "port (\d)/queue (\d{1,2}): received (\d) packets"
            qnum = self.element_strip(out, pattern)
            ptypes = packet_type.split('/')
            if flowtype in [23, 24, 26]:
                layerparams = ['L3_', 'TUNNEL_']
                endparams = ['_EXT_UNKNOWN', '']
            if flowtype in [28, 29, 30]:
                layerparams = ['L2_ETHER_', 'L3_', 'L4_']
                endparams = ['', '_EXT_UNKNOWN', '']
            for layerparam, ptype, endparam in zip(
                    layerparams, ptypes, endparams):
                layer_type = layerparam + ptype + endparam
                self.verify(
                    layer_type in out,
                    "Failed to output ptype information!!!")
            return qnum

    def pctype_flowtype_mapping(self, flowtype, pctype):
        """
        dynamic flowtype/pctype mapping for new protocol.
        """
        self.dut_testpmd.execute_cmd('port config 0 pctype mapping reset')
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
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')

    def run_rss_test(self, crlwords, flowtype, pctype, keywords, qchecks):
        """
        Use dynamic flowtype/pctype mapping, use default or dynamic change
        control words to set hash input configuration for new protocol
        RSS enabling, check RSS could work and keywords could control queue
        number.
        crlwords: control words of keyword.
        flowtype: define flow type 23~63 values for PPPoE and PPPoL2TPv2 packet
                  types as test plan table.
        pctype: profile defines 14~21 pctypes for PPPoE and PPPoL2TPv2 packet
                types.
        keywords: keywords have session ID, S-Port, D-Port, IP SA, IP DA and
                  etc.
        qchecks: define sameq and difq. If change keywords, direct packets to
                 different queue, otherwise direct packets to same queue.
        """

        self.pctype_flowtype_mapping(flowtype, pctype)
        if crlwords is not None:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd(
                'port config 0 pctype %s hash_inset clear all' % pctype)
            for word in crlwords:
                self.dut_testpmd.execute_cmd(
                    'port config 0 pctype %s hash_inset set field %s'
                    % (pctype, word))
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.execute_cmd('port config all rss %s' % flowtype)
        self.dut_testpmd.execute_cmd('start')
        qnum = self.send_and_verify(flowtype, 'def', 'rss')
        qdef = qnum
        for word, chk in zip(keywords, qchecks):
            qnum = self.send_and_verify(flowtype, word, 'rss')
            if qnum == qdef:
                result = 'sameq'
            elif qnum != qdef:
                result = 'difq'
            self.verify(result == chk,
                        "Faild to verify RSS when key word change!!!")

    def run_fd_test(self, crlwords, flowtype, pctype, keywords, qchecks):
        """
        Use dynamic flowtype/pctype mapping, use default or dynamic change
        control words to set flow director input configuration for new
        protocol, setup raw flow type filter for flow director, check flow
        director could work.
        crlwords: control words of keyword
        flowtype: define flow type 23~63 values for PPPoE and PPPoL2TPv2 packet
                  types as test plan table.
        pctype: profile defines below 14~21 pctypes for PPPoE and PPPoL2TPv2
                packet types.
        keywords: keywords have Session ID, S-Port, D-Port, IP SA, IP DA and
                  etc.
        qchecks: define sameq and difq. If change keywords, direct packets to
                 queue 0, otherwise direct packets to same queue.
        """

        self.pctype_flowtype_mapping(flowtype, pctype)
        if crlwords is not None:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd(
                'port config 0 pctype %s fdir_inset clear all' % pctype)
            for word in crlwords:
                self.dut_testpmd.execute_cmd(
                    'port config 0 pctype %s fdir_inset set field %s'
                    % (pctype, word))
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.execute_cmd('start')
        qnum = self.send_and_verify(flowtype, 'def', 'fd')
        self.verify(qnum == 0, "Receive packet from wrong queue!!!")
        self.raw_packet_generate(flowtype)
        queue = random.randint(1, self.PF_QUEUE - 1)
        self.dut_testpmd.execute_cmd(
            'flow_director_filter 0 mode raw add flow %d fwd queue %d \
            fd_id 1 packet /tmp/test.raw'
            % (flowtype, queue))
        qnum = self.send_and_verify(flowtype, 'def', 'fd')
        qdef = qnum
        self.verify(qnum == queue, "Receive packet from wrong queue!!!")
        for word, chk in zip(keywords, qchecks):
            qnum = self.send_and_verify(flowtype, word, 'fd')
            if qnum == qdef:
                result = 'sameq'
            elif qnum == 0:
                result = 'difq'
            self.verify(result == chk, "Faild to verify flow director when \
                key word change!!!")

    def test_rss_pppoe(self):
        """
        PPPoE is supported by NVM with profile updated. Download profile then
        set flowtype/pctype mapping, default hash input set are MAC SA and
        session ID, check RSS could work and queue could change when changing
        them.
        """
        crlwords = None
        keywords = ['session_id', 'src_mac', 'dst_mac']
        qchecks = ['difq', 'difq', 'sameq']
        self.run_rss_test(crlwords, 30, 17, keywords, qchecks)

    def test_rss_pppoe_ipv4(self):
        """
        PPPoE IPv4 is supported by NVM with profile updated. Download profile
        then set flowtype/pctype mapping, default hash input set are IPv4 SA,
        IPv4 DA, S-Port, D-Port, check RSS could work and queue could change
        when changing them.
        """
        crlwords = None
        keywords = ['src_ip', 'dst_ip', 'sport', 'dport', 'session_id']
        qchecks = ['difq', 'difq', 'difq', 'difq', 'sameq']
        self.run_rss_test(crlwords, 28, 15, keywords, qchecks)

    def test_rss_pppoe_ipv6(self):
        """
        PPPoE IPv6 is supported by NVM with profile updated. Download profile
        then set flowtype/pctype mapping, default hash input set are IPv6 SA,
        IPv6 DA, S-Port, D-Port, check RSS could work and queue could change
        when changing them.
        """
        crlwords = None
        keywords = ['src_ipv6', 'dst_ipv6', 'sport', 'dport', 'session_id']
        qchecks = ['difq', 'difq', 'difq', 'difq', 'sameq']
        self.run_rss_test(crlwords, 29, 16, keywords, qchecks)

    def test_rss_l2tp(self):
        """
        L2TPv2 PAY is supported by NVM with profile updated. Download profile
        then set flowtype/pctype mapping, default hash input set are MAC SA and
        session ID, check RSS could work and queue could change when changing
        them.
        """
        crlwords = None
        keywords = ['session_id', 'src_mac', 'dst_mac']
        qchecks = ['difq', 'difq', 'sameq']
        self.run_rss_test(crlwords, 26, 21, keywords, qchecks)

    def test_rss_pppoe_sessid(self):
        """
        PPPoE is supported by NVM with profile updated. Download profile then
        set flowtype/pctype mapping, dynamic to change hash input set
        configuration for session ID word 47, enable RSS, check RSS could
        work and queue could change when changing session ID.
        """
        crlwords = list(range(47, 48))
        keywords = ['session_id']
        qchecks = ['difq']
        self.run_rss_test(crlwords, 30, 17, keywords, qchecks)

    def test_rss_pppoe_srcmac(self):
        """
        PPPoE is supported by NVM with profile updated. Download profile then
        set flowtype/pctype mapping, dynamic to change hash input set
        configuration for source mac words 3~5, enable RSS, check RSS could
        work and queue could change when changing SA.
        """
        crlwords = list(range(3, 6))
        keywords = ['src_mac', 'dst_mac']
        qchecks = ['difq', 'sameq']
        self.run_rss_test(crlwords, 30, 17, keywords, qchecks)

    def test_rss_pppol2tp_ipv4(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, default hash input set are
        IPv4 SA, IPv4 DA, S-Port, D-Port, check RSS could work and queue
        could change when changing them.
        """
        crlwords = None
        keywords = ['src_ip', 'dst_ip', 'sport', 'dport', 'session_id']
        qchecks = ['difq', 'difq', 'difq', 'difq', 'sameq']
        self.run_rss_test(crlwords, 23, 18, keywords, qchecks)

    def test_rss_pppol2tp_inner_srcip(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, dynamic to change hash
        input set configuration for IPv4 SA words 15~16, enable RSS, check
        RSS could work and queue could change when changing IPv4 SA.
        """
        crlwords = list(range(15, 17))
        keywords = ['src_ip', 'dst_ip']
        qchecks = ['difq', 'sameq']
        self.run_rss_test(crlwords, 23, 18, keywords, qchecks)

    def test_rss_pppol2tp_inner_dstip(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, dynamic to change hash
        input set configuration for IPv4 DA words 27~28, enable RSS, check
        RSS could work and queue could change when changing IPv4 DA.
        """
        crlwords = list(range(27, 29))
        keywords = ['dst_ip', 'src_ip']
        qchecks = ['difq', 'sameq']
        self.run_rss_test(crlwords, 23, 18, keywords, qchecks)

    def test_rss_pppol2tp_sport(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, dynamic to change hash
        input set configuration for S-Port word 29, enable RSS, check
        RSS could work and queue could change when changing S-Port.
        """
        crlwords = list(range(29, 30))
        keywords = ['sport', 'dport']
        qchecks = ['difq', 'sameq']
        self.run_rss_test(crlwords, 23, 18, keywords, qchecks)

    def test_rss_pppol2tp_dport(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, dynamic to change hash
        input set configuration for D-Port word 30, enable RSS, check
        RSS could work and queue could change when changing D-Port.
        """
        crlwords = list(range(30, 31))
        keywords = ['dport', 'sport']
        qchecks = ['difq', 'sameq']
        self.run_rss_test(crlwords, 23, 18, keywords, qchecks)

    def test_fd_pppoe(self):
        """
        PPPoE is supported by NVM with profile updated. Download profile then
        set flowtype/pctype mapping, default flow director input set are MAC
        SA, session ID, setup raw flow type filter for flow director, check
        flow director could work when sending matched packets to configured
        queue, otherwise direct packets to queue 0.
        """
        crlwords = None
        keywords = ['src_mac', 'session_id', 'dst_mac']
        qchecks = ['difq', 'difq', 'sameq']
        self.run_fd_test(crlwords, 30, 17, keywords, qchecks)

    def test_fd_l2tp(self):
        """
        L2TPv2 PAY is supported by NVM with profile updated. Download profile
        then set flowtype/pctype mapping, default flow director input set are
        MAC SA, session ID, setup raw flow type filter for flow director, check
        flow director could work when sending matched packets to configured
        queue, otherwise direct packets to queue 0.
        """
        crlwords = None
        keywords = ['src_mac', 'session_id', 'dst_mac']
        qchecks = ['difq', 'difq', 'sameq']
        self.run_fd_test(crlwords, 26, 21, keywords, qchecks)

    def test_fd_pppoe_ipv4(self):
        """
        PPPoE IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, default flow director input
        set are IPv4 SA, IPv4 DA, S-Port, D-Port, setup raw flow type filter
        for flow director, check flow director could work when sending matched
        packets to configured queue, otherwise direct packets to queue 0.
        """
        crlwords = None
        keywords = ['src_ip', 'dst_ip', 'sport', 'dport', 'session_id']
        qchecks = ['difq', 'difq', 'difq', 'difq', 'sameq']
        self.run_fd_test(crlwords, 28, 15, keywords, qchecks)

    def test_fd_pppoe_ipv6(self):
        """
        PPPoE IPv6 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, default flow director input
        set are IPv6 SA, IPv6 DA, S-Port, D-Port, setup raw flow type filter
        for flow director, check flow director could work when sending matched
        packets to configured queue, otherwise direct packets to queue 0.
        """
        crlwords = None
        keywords = ['src_ipv6', 'dst_ipv6', 'sport', 'dport', 'session_id']
        qchecks = ['difq', 'difq', 'difq', 'difq', 'sameq']
        self.run_fd_test(crlwords, 29, 16, keywords, qchecks)

    def test_fd_pppol2tp_ipv4(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, default flow director input
        set are IPv4 SA, IPv4 DA, S-Port, D-Port, setup raw flow type filter
        for flow director, check flow director could work when sending matched
        packets to configured queue, otherwise direct packets to queue 0.
        """
        crlwords = None
        keywords = ['src_ip', 'dst_ip', 'sport', 'dport']
        qchecks = ['difq', 'difq', 'difq', 'difq']
        self.run_fd_test(crlwords, 23, 18, keywords, qchecks)

    def test_fd_pppol2tp_ipv6(self):
        """
        PPPoL2TPv2 IPv6 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, default flow director input
        set are IPv6 SA, IPv6 DA, S-Port, D-Port, setup raw flow type filter
        for flow director, check flow director could work when sending matched
        packets to configured queue, otherwise direct packets to queue 0.
        """
        crlwords = None
        keywords = ['src_ipv6', 'dst_ipv6', 'sport', 'dport']
        qchecks = ['difq', 'difq', 'difq', 'difq']
        self.run_fd_test(crlwords, 24, 19, keywords, qchecks)

    def test_fd_pppol2tp_ipv4_dstip(self):
        """
        PPPoL2TPv2 IPv4 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, dynamic to change flow
        director input set configuration for IPv4 DA words 27~28, setup
        raw flow type filter for flow director, check flow director could
        work when sending matched IPv4 DA packets to configured queue,
        otherwise direct packets to queue 0.
        """
        crlwords = list(range(27, 29))
        keywords = ['src_ip', 'sport', 'dport', 'dst_ip']
        qchecks = ['sameq', 'sameq', 'sameq', 'difq']
        self.run_fd_test(crlwords, 23, 18, keywords, qchecks)

    def test_fd_pppol2tp_ipv6_dstipv6(self):
        """
        PPPoL2TPv2 IPv6 is supported by NVM with profile updated. Download
        profile then set flowtype/pctype mapping, dynamic to change flow
        director input set configuration for IPv6 DA words 21~28, setup
        raw flow type filter for flow director, check flow director could
        work when sending matched IPv6 DA packets to configured queue,
        otherwise direct packets to queue 0.
        """
        crlwords = list(range(21, 29))
        keywords = ['src_ipv6', 'sport', 'dport', 'dst_ipv6']
        qchecks = ['sameq', 'sameq', 'sameq', 'difq']
        self.run_fd_test(crlwords, 24, 19, keywords, qchecks)

    def tear_down(self):
        self.dut_testpmd.execute_cmd('stop')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        if "Profile number is: 0" not in out:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd('ddp del 0 /tmp/ppp-oe-ol2tpv2.bak')
            out = self.dut_testpmd.execute_cmd('ddp get list 0')
            self.verify("Profile number is: 0" in out,
                        "Failed to delete ddp profile!!!")
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.quit()

    def tear_down_all(self):
        pass
