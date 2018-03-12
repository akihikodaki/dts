# <COPYRIGHT_TAG>

import time
import re
import sys
import utils
from test_case import TestCase
from pmd_output import PmdOutput
from settings import get_nic_name


class TestDdpGtpQregion(TestCase):

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        profile_file = 'dep/gtp.pkgo'
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
        self.flowtype_qregion_mapping()

    def element_strip(self, out, pattern):
        """
        Strip and get queue number.
        """
        s = re.compile(pattern)
        res = s.search(out)
        if res is None:
            print utils.RED('Search no queue number.')
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
        self.dut_testpmd.execute_cmd('ddp add 0 /tmp/gtp.pkgo,/tmp/gtp.bak')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        self.verify("Profile number is: 1" in out,
                    "Failed to load ddp profile!!!")
        self.dut_testpmd.execute_cmd('port start all')

    def flowtype_qregion_mapping(self):
        """
        Queue region, queue range and flow type mapping set according to
        mapping table.
        """
        rg_ids = [0, 1, 2, 3]
        idx_ids = [1, 10, 30, 40]
        q_nums = [8, 16, 8, 16]
        flowtypes = [26, 23, 24, 25]
        for rg_id, idx_id, q_num in zip(rg_ids, idx_ids, q_nums):
            self.dut_testpmd.execute_cmd('set port 0 queue-region region_id \
                %d queue_start_index %d queue_num %d' % (rg_id, idx_id, q_num))
        for rg_id, flowtype in zip(rg_ids, flowtypes):
            self.dut_testpmd.execute_cmd('set port 0 queue-region region_id \
                %d flowtype %d' % (rg_id, flowtype))
        self.dut_testpmd.execute_cmd('set port 0 queue-region flush on')

    def gtp_pkts(self, flowtype, keyword, opt):
        """
        Generate GTP packets.
        """
        src_ip = "1.1.1.1"
        dst_ip = "2.2.2.2"
        src_ipv6 = "1001:0db8:85a3:0000:0000:8a2e:0370:0001"
        dst_ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:0001"
        teid = hex(0xfe)
        sport = 100
        dport = 200
        if opt is not 'word_opt':
            if keyword is 'src_ip':
                src_ip = "1.1.1.2"
            if keyword is 'dst_ip':
                dst_ip = "2.2.2.3"
            if keyword is 'src_ipv6':
                src_ipv6 = "1001:0db8:85a3:0000:0000:8a2e:0370:0002"
            if keyword is 'dst_ipv6':
                dst_ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:0002"
            if keyword is 'teid':
                teid = hex(0xff)
            if keyword is 'sport':
                sport = 101
            if keyword is 'dport':
                dport = 201

        if flowtype == 23:
            pkts = {'IPV6/GTPU/IPV6/UDP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=%s)/IPv6(src="%s",dst="%s")/UDP(sport=%d,dport=%d)/Raw("X"*20)'
                    % (teid, src_ipv6, dst_ipv6, sport, dport)}
        if flowtype == 25:
            pkts = {'IPV6/GTPC': 'Ether()/IPv6(src="%s",dst="%s")/UDP(dport=2123)/GTP_U_Header(teid=%s)/Raw("X"*20)'
                    % (src_ipv6, dst_ipv6, teid)}
        if flowtype == 26:
            pkts = {'IPV6/GTPU/IPV4/UDP': 'Ether()/IPv6()/UDP(dport=2152)/GTP_U_Header(teid=%s)/IP(src="%s",dst="%s")/UDP(sport=%d,dport=%d)/Raw("X"*20)'
                    % (teid, src_ip, dst_ip, sport, dport)}
        return pkts

    def send_and_verify(self, flowtype, qmin, qmax, keyword):
        """
        Send packets and verify result.
        opt has below three scenarios:
        word_opt: check RSS could work when enable words for keyword.
        chgword_opt: change keyword value, e.g. check dst controls queue
                     number, change dst then check pmd could receive packet
                     from different queue.
        notword_opt: change not keyword, e.g. check dst controls queue number,
                     change src then check pmd receives packet from same queue.
        """
        for opt in ['word_opt', 'chgword_opt', 'notword_opt']:
            if opt is 'notword_opt':
                if keyword is 'teid' or keyword is 'sport' or \
                        keyword is 'dport':
                    break
                elif keyword == 'src_ip':
                    keyword = 'dst_ip'
                elif keyword == 'dst_ip':
                    keyword = 'src_ip'
                elif keyword == 'src_ipv6':
                    keyword = 'dst_ipv6'
                elif keyword == 'dst_ipv6':
                    keyword = 'src_ipv6'
            pkts = self.gtp_pkts(flowtype, keyword, opt)
            for packet_type in pkts.keys():
                self.tester.scapy_append(
                    'sendp([%s], iface="%s")'
                    % (pkts[packet_type], self.tester_intf))
                self.tester.scapy_execute()
                out = self.dut.get_session_output(timeout=2)
                self.verify("PKT_RX_RSS_HASH" in out, "Failed to test RSS!!!")
                pattern = "port (\d)/queue (\d{1,2}): received (\d) packets"
                qnum = self.element_strip(out, pattern)
                if opt is 'word_opt':
                    crol_qnum = qnum
                layerparams = ['L3_', 'TUNNEL_',
                               'INNER_L3_', 'INNER_L4_']
                ptypes = packet_type.split('/')
                endparams = ['_EXT_UNKNOWN', '',
                             '_EXT_UNKNOWN', '']
                for layerparam, ptype, endparam in zip(
                        layerparams, ptypes, endparams):
                    layer_type = layerparam + ptype + endparam
                    self.verify(
                        layer_type in out,
                        "Failed to output ptype information!!!")
                self.verify(qnum <= qmax and qnum >= qmin,
                            "Queue is not between this queue range!!!")
                if opt is 'chgword_opt':
                    self.verify(qnum != crol_qnum,
                                "Failed to test rss if changing key words!!!")
                if opt is 'notword_opt':
                    self.verify(qnum == crol_qnum,
                                "Failed to test rss if changing to other key \
                                words!!!")

    def run_gtp_test(self, crlwords, flowtype, pctype, qmin, qmax, keyword):
        """
        Use dynamic flowtype/pctype mapping, queue region, dynamic change
        control words to set hash input configuration for new protocol
        GTP RSS enabling, check keyword could control queue number in
        configured queue regon.
        crlwords: control words of keyword
        flowtype: define flow type 26, 23, 24, 25 for GTP types as below
                  table, check each layer type, tunnel packet includes
                  GTPC and GTPU, GTPC has none inner L3, GTPU has none,
                  IPV4 and IPV6 inner L3.
        pctype: profile defines below 22, 23, 24, 25 pctypes for GTP packet
                types.
        qmin: design queue minimum value for the flowtype in queue region.
        qmax: design queue maximum value for the flowtype in queue region.
        keyword: keyword has teid, sport, dport, src, dst, etc.

        +-------------+------------+------------+--------------+-------------+
        | Packet Type |   PCTypes  | Flow Types | Queue region | Queue range |
        +-------------+------------+------------+--------------+-------------+
        | GTP-U IPv4  |     22     |    26      |      0       |     1~8     |
        +-------------+------------+------------+--------------+-------------+
        | GTP-U IPv6  |     23     |    23      |      1       |     10~25   |
        +-------------+------------+------------+--------------+-------------+
        | GTP-U PAY4  |     24     |    24      |      2       |     30~37   |
        +-------------+------------+------------+--------------+-------------+
        | GTP-C PAY4  |     25     |    25      |      3       |     40~55   |
        +-------------+------------+------------+--------------+-------------+
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
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')
        self.send_and_verify(flowtype, qmin, qmax, keyword)

    def test_outer_dst_contrl_gtpcq(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash input
        set configuration for outer dst mac words 50~57, enable rss, check
        outer dst could control queue, also queue number is between the queue
        range(40,55).
        """
        crlwords = range(50, 58)
        self.run_gtp_test(crlwords, 25, 25, 40, 55, "dst_ipv6")

    def test_teid_contrl_gtpcq(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash input
        set configuration for teid words 44~45, enable rss, check teid could
        control queue, also queue number is between the queue range(40,55).
        """
        crlwords = range(44, 46)
        self.run_gtp_test(crlwords, 25, 25, 40, 55, "teid")

    def test_teid_contrl_gtpu_ipv4q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for teid words 44~45, enable rss, check teid
        could control queue, also queue number is between the queue
        range(1,8).
        """
        crlwords = range(44, 46)
        self.run_gtp_test(crlwords, 26, 22, 1, 8, "teid")

    def test_sport_contrl_gtpu_ipv4q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for sport words 29~30, enable rss, check
        sport could control queue, also queue number is between the queue
        range(1,8).
        """
        crlwords = range(29, 31)
        self.run_gtp_test(crlwords, 26, 22, 1, 8, "sport")

    def test_dport_contrl_gtpu_ipv4q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for dport words 29~30, enable rss, check
        dport could control queue, also queue number is between the queue
        range(1,8).
        """
        crlwords = range(29, 31)
        self.run_gtp_test(crlwords, 26, 22, 1, 8, "dport")

    def test_inner_src_contrl_gtpu_ipv4q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for inner src words 15~16, enable rss, check
        inner src could control queue, also queue number is between the
        queue range(1,8).
        """
        crlwords = range(15, 17)
        self.run_gtp_test(crlwords, 26, 22, 1, 8, "src_ip")

    def test_inner_dst_contrl_gtpu_ipv4q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for inner dst words 27~28, enable rss, check
        inner dst could control queue, also queue number is between the queue
        range(1,8).
        """
        crlwords = range(27, 29)
        self.run_gtp_test(crlwords, 26, 22, 1, 8, "dst_ip")

    def test_teid_contrl_gtpu_ipv6q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for teid words 44~45, enable rss, check teid
        could control queue, also queue number is between the queue
        range(10,25).
        """
        crlwords = range(44, 46)
        self.run_gtp_test(crlwords, 23, 23, 10, 25, "teid")

    def test_sport_contrl_gtpu_ipv6q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for sport words 29~30, enable rss, check
        sport could control queue, also queue number is between the queue
        range(10,25).
        """
        crlwords = range(29, 31)
        self.run_gtp_test(crlwords, 23, 23, 10, 25, "sport")

    def test_dport_contrl_gtpu_ipv6q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for dport words 29~30, enable rss, check
        dport could control queue, also queue number is between the queue
        range(10,25).
        """
        crlwords = range(29, 31)
        self.run_gtp_test(crlwords, 23, 23, 10, 25, "dport")

    def test_inner_src_contrl_gtpu_ipv6q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for inner src words 13~20, enable rss, check
        inner src could control queue, also queue number is between the queue
        range(10,25).
        """
        crlwords = range(13, 21)
        self.run_gtp_test(crlwords, 23, 23, 10, 25, "src_ipv6")

    def test_inner_dst_contrl_gtpu_ipv6q(self):
        """
        GTP is supported by NVM with profile updated. Download profile then
        set queue region/flowtype/pctype mapping, dynamic to change hash
        input set configuration for inner dst words 21~28, enable rss, check
        inner dst could control queue, also queue number is between the queue
        range(10,25).
        """
        crlwords = range(21, 29)
        self.run_gtp_test(crlwords, 23, 23, 10, 25, "dst_ipv6")

    def tear_down(self):
        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.execute_cmd('set port 0 queue-region flush off')
        out = self.dut_testpmd.execute_cmd('ddp get list 0')
        if "Profile number is: 0" not in out:
            self.dut_testpmd.execute_cmd('port stop all')
            time.sleep(1)
            self.dut_testpmd.execute_cmd('ddp del 0 /tmp/gtp.bak')
            out = self.dut_testpmd.execute_cmd('ddp get list 0')
            self.verify("Profile number is: 0" in out,
                        "Failed to delete ddp profile!!!")
            self.dut_testpmd.execute_cmd('port start all')
        self.dut_testpmd.execute_cmd('write reg 0 0xb8190 1')
        self.dut_testpmd.execute_cmd('write reg 0 0xb8190 2')
        self.dut_testpmd.quit()

    def tear_down_all(self):
        pass
